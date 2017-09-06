#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device.py
@time: 2017/8/29 20:59
"""

from datetime import datetime

from exts.base import Base
from exts.database import db


# 设备信息
class Device(Base):
    __tablename__ = 'device'

    # 使用状态
    STATE_VALUES = ('unused', 'using')

    # 设备ID
    id = db.Column(db.Integer, primary_key=True)

    # 设备机器码
    machine_code = db.Column(db.String(128), index=True)

    # 设备名称
    name = db.Column(db.String(128), unique=True, index=True)

    # # 投放地址
    # address = db.Column(db.String(128), nullable=False)
    # 省份信息
    province = db.Column(db.String(16), nullable=False)

    # 市级信息
    city = db.Column(db.String(64), nullable=False)

    # 区域信息
    area = db.Column(db.String(64), nullable=False)

    # 详细地址信息
    location = db.Column(db.String(128), nullable=False)

    # 设备收入
    income = db.Column(db.Integer, nullable=False, default=0)

    # 设备当前使用状态 0 未使用 1 正在使用
    state = db.Column(db.Enum(*STATE_VALUES), nullable=False, index=True, default='unused')

    # 创建时间
    ctime = db.Column(db.DateTime(), default=datetime.utcnow)

    # 数据更新时间
    utime = db.Column(db.DateTime(), default=datetime.utcnow)

    @classmethod
    def create(cls, name, machine_code,
               province, city, area, location):
        device = cls(
            name=name,
            machine_code=machine_code,
            province=province,
            city=city,
            area=area,
            location=location)
        db.session.add(device)
        db.session.commit()
        return device

    def __repr__(self):
        return '<Device {}>'.format(self.name)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'machine_code': self.machine_code,
            'province': self.province,
            'city': self.city,
            'area': self.area,
            'location': self.location,
            'income': self.income,
            'state': self.state,
            'utime': self.utime,
            'ctime': self.ctime,
        }