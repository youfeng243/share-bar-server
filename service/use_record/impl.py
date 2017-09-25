#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/9/25 00:23
"""
from datetime import datetime

from exts.common import log
from exts.database import db
from service.device.model import Device
from service.use_record.model import UseRecord
from service.user.model import User


class UseRecordService(object):
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
