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
from exts.model_base import ModelBase


class Recharge(ModelBase):
    __tablename__ = 'recharge'

    # 用户ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # 充值流水账号 每一次充值带时间戳的唯一ID
    transaction_id = db.Column(db.String(64), unique=True, index=True, nullable=False)

    # 充值金额
    amount = db.Column(db.Integer, index=True, nullable=False)

    # 付款时间
    pay_time = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return '<Recharge {} {}>'.format(self.username, self.dev_name)

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict(),
            'amount': self.amount,
            'transaction_id': self.transaction_id,
            'pay_time': self.pay_time.strftime('%Y-%m-%d %H:%M:%S'),
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }
