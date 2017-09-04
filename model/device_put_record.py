#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device_put_record.py
@time: 2017/8/29 21:26
"""
from datetime import datetime

from common import db


# 设备投放记录 只读记录，写入一次 不需要再修改
class DevicePutRecord(db.Model):
    __tablename__ = 'device_put_record'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 设备名称
    dev_name = db.Column(db.String(128), unique=True, index=True)

    # 投放地址
    put_address = db.Column(db.String(128), nullable=False)

    # 数据被创建的时间
    in_time = db.Column(db.DateTime(), nullable=False)

    # 数据更新时间
    update_time = db.Column(db.DateTime(), nullable=False)

    def __init__(self, dev_name, put_address):
        self.dev_name = dev_name
        self.put_address = put_address
        self.update_time = self.in_time = datetime.now()

    # 更新数据时间
    def update(self):
        self.update_time = datetime.now()

    def __repr__(self):
        return '<DevicePutRecord {}>'.format(self.dev_name)


db.create_all()
