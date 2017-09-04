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


# 用户充值记录
class RechargeRecord(db.Model):
    __tablename__ = 'recharge_record'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 用户名
    username = db.Column(db.String(128), index=True, nullable=False)

    # 充值金额
    recharge_money = db.Column(db.Integer, nullable=False)

    # 数据被创建的时间
    in_time = db.Column(db.DateTime(), nullable=False)

    # 数据更新时间
    update_time = db.Column(db.DateTime(), nullable=False)

    def __init__(self, username, recharge_money):
        self.username = username
        self.recharge_money = recharge_money
        self.update_time = self.in_time = datetime.now()

    # 更新数据时间
    def update(self):
        self.update_time = datetime.now()

    def __repr__(self):
        return '<RechargeRecord {} {}>'.format(self.username, self.dev_name)


db.create_all()
