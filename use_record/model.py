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


# 用户和设备使用记录
class UseRecord(db.Model):
    __tablename__ = 'use_record'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 用户名
    user_id = db.Column(db.Integer, index=True, nullable=False)

    # 设备号
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
    end_time = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    # 开机时间
    ctime = db.Column(db.DateTime(), default=datetime.utcnow)

    # 数据更新时间
    utime = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return '<UseRecord {} {}>'.format(self.user_id, self.device_id)
