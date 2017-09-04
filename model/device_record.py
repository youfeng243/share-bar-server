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

from common import db


# 使用记录表，用户使用记录 设备使用记录 统一的表
# 只读记录，写入一次 不需要再修改
class DeviceRecord(db.Model):
    __tablename__ = 'device_record'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 用户名
    username = db.Column(db.String(128), index=True, nullable=False)

    # 设备号
    dev_name = db.Column(db.String(128), index=True, nullable=False)

    # 手机号码
    telephone = db.Column(db.String(64), index=True, nullable=False)

    # 使用地点
    put_address = db.Column(db.String(128), nullable=False)

    # 花费的金额
    cost_money = db.Column(db.Integer, nullable=False)

    # 开机时间
    start_time = db.Column(db.DateTime(), nullable=False)

    # 下机时间
    end_time = db.Column(db.DateTime(), nullable=False)

    # 数据被创建的时间
    in_time = db.Column(db.DateTime(), nullable=False)

    # 数据更新时间
    update_time = db.Column(db.DateTime(), nullable=False)

    def __init__(self, username, dev_name, telephone, put_address, cost_money, start_time, end_time):
        self.username = username
        self.dev_name = dev_name
        self.telephone = telephone
        self.put_address = put_address
        self.cost_money = cost_money
        self.start_time = start_time
        self.end_time = end_time
        self.update_time = self.in_time = datetime.now()

    # 更新数据时间
    def update(self):
        self.update_time = datetime.now()

    def __repr__(self):
        return '<DeviceRecord {} {}>'.format(self.username, self.dev_name)


db.create_all()
