#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/9/26 16:22
"""
import json
from datetime import datetime

from exts.common import log, fail, HTTP_OK, success
from exts.database import redis, db
from exts.redis_dao import get_record_key, get_device_key, get_token_key
from exts.redis_dao import get_user_key
from service.device.model import Device
from service.use_record.model import UseRecord
from service.user.model import User


class WindowsService(object):
    @staticmethod
    def cal_offline(user_id, device_id, record_id, charge_mode):
        try:
            # 获得用户信息
            user = User.get(user_id)

            # 获得设备信息
            device = Device.get(device_id)

            # 获得试用记录
            record = UseRecord.get(record_id)

            # 记录下机时间
            record.end_time = datetime.now()

            # 设置设备为空闲状态
            device.state = Device.STATE_FREE

            # 计算花费时间
            record.cost_time = (record.end_time - record.ctime).seconds // 60

            # 计算花费金钱
            record.cost_money = record.cost_time * charge_mode

            # 计算设备获得的金钱数目
            device.income += record.cost_money

            # 计算用户花费的钱
            user.balance_account -= record.cost_money
            if user.balance_account < 0:
                user.balance_account = 0
            user.used_account += record.cost_money

            db.session.add(user)
            db.session.add(device)
            db.session.add(record)
            db.session.commit()
        except Exception as e:
            log.error("未知错误: user_id = {} device_id = {} record_id = {}".format(user_id, device_id, record_id))
            log.exception(e)
            db.session.rollback()
            return False

        return True

    @staticmethod
    def logout(charging):
        try:
            charge_dict = json.loads(charging)
            record_id = charge_dict.get('id')
            user_id = charge_dict.get('user_id')
            device_id = charge_dict.get('device_id')
            charge_mode = charge_dict.get('charge_mode')
            device_code = charge_dict.get('device_code')
            log.info("当前下线信息: user_id = {} device_id = {} charge_mode = {} device_code = {}".format(
                user_id, device_id, charge_mode, device_code))

            # 结账下机
            if not WindowsService.cal_offline(user_id=user_id,
                                              device_id=device_id,
                                              record_id=record_id,
                                              charge_mode=charge_mode):
                log.error("下机扣费失败: user_id = {} device_id = {} charge_mode = {}".format(
                    user_id, device_id, charge_mode))
                return fail(HTTP_OK, u"下机失败！")

                # 判断是否已经在redis中进行记录
            record_key = get_record_key(user_id, device_id)
            # 获得用户上线key
            user_key = get_user_key(user_id)
            # 获得设备上线key
            device_key = get_device_key(device_id)
            # 获得当前设备token
            token_key = get_token_key(device_code)

            # 从redis中删除上机记录
            redis.delete(record_key)
            redis.delete(user_key)
            redis.delete(device_key)
            redis.delete(token_key)

        except Exception as e:
            log.error("数据解析失败: {}".format(charging))
            log.exception(e)
            return fail(HTTP_OK, u"数据解析失败!!")
        log.info("下机成功: user_id = {} device_id = {}".format(user_id, device_id))
        return success({'status': 1, 'msg': 'logout successed!'})
