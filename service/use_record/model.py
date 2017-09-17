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

from exts.database import db
from exts.model_base import ModelBase
from service.device.model import Device
from service.user.model import User


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
    cost_money = db.Column(db.Integer, nullable=False, default=0)

    # 下机时间 数据初始化时以创建时间为结束时间
    end_time = db.Column(db.DateTime, nullable=False, default=datetime.now())

    def __repr__(self):
        return '<UseRecord {} {}>'.format(self.user_id, self.device_id)

    def to_dict(self):

        to_json = {
            'province': self.province,
            'city': self.city,
            'area': self.area,
            'location': self.location,
            'cost_money': self.cost_money,
            'ctime': self.ctime,
            'utime': self.utime,
            'end_time': self.end_time,
            'cost_time': round((self.end_time - self.ctime).seconds / 60.0, 1)  # 分钟
        }

        item = User.get(self.user_id)
        if item is not None:
            to_json['user'] = item.to_dict()
        item = Device.get(self.device_id)
        if item is not None:
            to_json['device'] = item.to_dict()

        return to_json
