#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: addr_manage.py
@time: 2017/8/30 08:49
"""
from datetime import datetime

from common import db


# 投放地址管理 需要写入统计设备信息
class AddrManage(db.Model):
    __tablename__ = 'addr_manage'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 地址ID 这个貌似不需要
    # addr_id = db.Column(db.String(64), unique=True, nullable=False)

    # 地址信息
    address = db.Column(db.String(256), unique=True, index=True, nullable=False)

    # 统计设备数目
    device_num = db.Column(db.Integer, nullable=False)

    # 生效时间
    effective_date = db.Column(db.DateTime(), nullable=False)

    # # 数据被创建的时间
    # in_time = db.Column(db.DateTime(), nullable=False)

    # 数据更新时间
    update_time = db.Column(db.DateTime(), nullable=False)

    def __init__(self, address, device_num):
        # self.addr_id = addr_id
        self.address = address
        self.device_num = device_num
        self.update_time = self.effective_date = datetime.now()

    # 更新数据时间
    def update(self):
        self.update_time = datetime.now()

    def __repr__(self):
        return '<AddrManage {}>'.format(self.addr_id)


# db.drop_all()
db.create_all()
