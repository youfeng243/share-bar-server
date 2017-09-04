#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device.py
@time: 2017/8/29 20:59
"""

# 设备信息
from datetime import datetime

from common import db


class Device(db.Model):
    __tablename__ = 'devices'

    # 设备ID
    id = db.Column(db.Integer, primary_key=True)

    # 设备名称
    dev_name = db.Column(db.String(128), unique=True, index=True)

    # 投放地址
    put_address = db.Column(db.String(128), nullable=False)

    # 设备收入
    income = db.Column(db.Integer, nullable=False)

    # 设备当前使用状态 0 未使用 1 正在使用
    use_state = db.Column(db.Integer, nullable=False, index=True)

    # 数据被创建的时间
    in_time = db.Column(db.DateTime(), nullable=False)

    # 数据更新时间
    update_time = db.Column(db.DateTime(), nullable=False)

    def __init__(self, dev_name, put_address, income, use_state):
        self.dev_name = dev_name
        self.put_address = put_address
        self.income = income
        self.use_state = use_state
        self.update_time = self.in_time = datetime.now()

    # 更新数据时间
    def update(self):
        self.update_time = datetime.now()

    def __repr__(self):
        return '<Device {}>'.format(self.dev_name)


# db.drop_all()
db.create_all()
