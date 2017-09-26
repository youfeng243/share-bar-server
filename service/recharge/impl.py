#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/9/25 00:18
"""
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from exts.common import log
from exts.database import db
from service.recharge.model import Recharge
from service.user.model import User


class RechargeService(object):
    @staticmethod
    def create(user_id, amount, transaction_id, pay_time):
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
