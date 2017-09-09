#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device.py
@time: 2017/8/29 20:59
"""

from exts.base import Base
from exts.database import db


# 设备信息
class Device(Base):
    __tablename__ = 'device'

    # 使用状态
    STATE_VALUES = ('free', 'busy', 'offline')

    # 设备机器码
    device_code = db.Column(db.String(128), unique=True, index=True)

    # 投放ID
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))

    # 部署记录
    deploy_list = db.relationship('Deploy', backref='device', lazy='dynamic')

    # 设备收入
    income = db.Column(db.Integer, nullable=False, default=0)

    # 设备当前使用状态 free 空闲 busy 忙碌  offline 离线
    state = db.Column(db.Enum(*STATE_VALUES), nullable=False, index=True, default='free')

    @classmethod
    def create(cls, device_code, address_id):
        device = cls(device_code=device_code, address_id=address_id)
        db.session.add(device)
        db.session.commit()
        return device

    # 通过设备编号获取设备信息
    @classmethod
    def get_device_by_code(cls, device_code):
        return cls.query.filter_by(device_code=device_code).first()

    def __repr__(self):
        return '<Device {}>'.format(self.name)

    def to_dict(self):
        return {
            'id': self.id,
            'device_code': self.device_code,
            'address_id': self.address_id,
            'income': self.income,
            'state': self.state,
            'utime': self.utime.strftime('%Y-%m-%d %H:%I:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%I:%S'),
        }
