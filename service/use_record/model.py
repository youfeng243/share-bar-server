#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device_record.py
@time: 2017/8/29 21:16
"""
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from exts.common import log
from exts.database import db
from exts.model_base import ModelBase
from service.device.model import Device
from service.user import User


class UseRecord(ModelBase):
    __tablename__ = 'use_record'

    # 用户名
    user_id = db.Column(db.Integer, index=True, nullable=False)

    # 设备ID
    device_id = db.Column(db.Integer, index=True, nullable=False)

    # 省份信息
    province = db.Column(db.String(16), nullable=False)

    # 市级信息
    city = db.Column(db.String(64), nullable=False)

    # 区域信息
    area = db.Column(db.String(64), nullable=False)

    # 详细地址信息
    location = db.Column(db.String(128), nullable=False)

    # 花费的金额
    cost_money = db.Column(db.Integer, nullable=False, index=True, default=0)

    # 下机时间 数据初始化时以创建时间为结束时间
    end_time = db.Column(db.DateTime, nullable=False, default=datetime.now())

    # 花费时间 秒为单位
    cost_time = db.Column(db.Integer, nullable=False, index=True, default=0)

    @classmethod
    def create(cls, user_id, device_id, province, city, area, location):
        use_record = cls(user_id=user_id, device_id=device_id,
                         province=province, city=city,
                         area=area, location=location)
        try:
            db.session.add(use_record)
            db.session.commit()
        except IntegrityError:
            log.error("未知错误: {} {}".format(user_id, device_id))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: {} {}".format(user_id, device_id))
            log.exception(e)
            return None, False
        return use_record, True

    def __repr__(self):
        return '<UseRecord {} {}>'.format(self.user_id, self.device_id)

    @classmethod
    def cal_offline(cls, user_id, device_id, record_id):
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
            record.cost_money = record.cost_time * device.charge_mode

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

    def to_dict(self):

        to_json = {
            'id': self.id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'province': self.province,
            'city': self.city,
            'area': self.area,
            'location': self.location,
            'cost_money': self.cost_money,
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'cost_time': self.cost_time // 60  # 分钟
        }

        item = User.get(self.user_id)
        if item is not None:
            to_json['user'] = item.to_dict()
        item = Device.get(self.device_id)
        if item is not None:
            to_json['device'] = item.to_dict()

        return to_json
