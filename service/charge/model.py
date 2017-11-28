#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: admin_manage.py
@time: 2017/8/30 09:10
"""

from exts.model_base import ModelBase
from exts.resource import db
from service.device.model import Device

__all__ = ['Device']


# 管理员信息
class Charge(ModelBase):
    __tablename__ = 'charge'

    # 费率模板名称
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # 费率  分钱/分钟
    charge_mode = db.Column(db.Integer, nullable=False)

    # 反向指向设备列表信息
    device_query = db.relationship('Device', backref='charge', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'charge_mode': self.charge_mode,
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }
