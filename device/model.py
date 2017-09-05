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

from exts.database import db


class Device(db.Model):
    __tablename__ = 'device'

    # 使用状态
    STATE_VALUES = ('unused', 'using')

    # 设备ID
    id = db.Column(db.Integer, primary_key=True)

    # 设备名称
    name = db.Column(db.String(128), unique=True, index=True)

    # 投放地址
    address = db.Column(db.String(128), nullable=False)

    # 设备收入
    income = db.Column(db.Integer, nullable=False, default=0)

    # 设备当前使用状态 0 未使用 1 正在使用
    state = db.Column(db.Enum(*STATE_VALUES), nullable=False, index=True, default='unused')

    # 管理员创建时间
    ctime = db.Column(db.DateTime(), default=datetime.utcnow)

    # 数据更新时间
    utime = db.Column(db.DateTime(), default=datetime.utcnow)

    @classmethod
    def create(cls, name, address):
        device = cls(
            name=name,
            address=address)
        db.session.add(device)
        db.session.commit()
        return device

    @classmethod
    def get(cls, a_id):
        return cls.query.get(a_id)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    # 删除数据
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    # 更新下修改时间
    def save(self):
        self.utime = datetime.now()
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return '<Device {}>'.format(self.name)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'income': self.income,
            'state': self.state,
            'utime': self.utime,
            'ctime': self.ctime,
        }
