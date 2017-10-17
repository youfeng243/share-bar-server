#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/9/25 00:18
"""
import json
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from exts.distributed_lock import Lock
from exts.common import log
from exts.resource import db, redis_client
from exts.redis_api import get_user_key
from service.recharge.model import Recharge
from service.template.impl import TemplateService
from service.user.model import User


class RechargeService(object):
    @staticmethod
    def create(user_id, amount, transaction_id, pay_time):
        amount = int(amount)
        user_id = int(user_id)
        recharge = Recharge(user_id=user_id,
                            amount=amount,
                            transaction_id=transaction_id,
                            pay_time=pay_time)

        # 账户总额增加
        user = User.get(user_id)
        if user is None:
            log.warn("当前充值用户信息不存在: user_id = {}".format(user_id))
            return None, False

        try:
            user.balance_account += amount
            user.total_account += amount
            user.utime = datetime.now()
            db.session.add(user)
            db.session.add(recharge)
            db.session.commit()

            # 发送充值成功通知
            TemplateService.recharge_remind(user.openid, pay_time, amount)

        except IntegrityError:
            log.error("主键重复: user_id = {} amount = {}".format(
                user_id, amount))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: user_id = {} amount = {}".format(
                user_id, amount))
            log.exception(e)
            return None, False
        return recharge, True

    @staticmethod
    def find_by_transaction_id(transaction_id):
        return Recharge.query.filter_by(transaction_id=transaction_id).first()

    # 给指定在线用户充值
    @staticmethod
    def online_recharge(user_id, total_fee):
        # 先获得用户缓存的信息
        user_key = get_user_key(user_id)

        # todo 这里需要加锁, 否则扣费下机时会有影响
        lock = Lock(user_key, redis_client)

        try:
            lock.acquire()
            record_key = redis_client.get(user_key)
            if record_key is None:
                log.info("当前用户没有在线 record_key = None, 不需要同步在线数据: user_id = {}".format(user_id))
                return

            charge_str = redis_client.get(record_key)
            if charge_str is None:
                log.info("当前用户没有在线 charging = None, 不需要同步在线数据: user_id = {}".format(user_id))
                return

            try:
                charge_dict = json.loads(charge_str)
                if charge_dict is None:
                    log.error("解析json数据失败: {}".format(charge_str))
                    return

                balance_account = charge_dict.get('balance_account')
                if not isinstance(balance_account, int):
                    log.error("balance_account 数据类型不正确: {}".format(balance_account))
                    return

                charge_dict['balance_account'] = balance_account + total_fee
                redis_client.set(record_key, json.dumps(charge_dict))

                log.info(
                    "同步修改redis中用户余额信息成功! user_id = {} account = {}".format(user_id, balance_account + total_fee))
            except Exception as e:
                log.error("解析json数据失败: {}".format(charge_str))
                log.exception(e)
        finally:
            lock.release()
