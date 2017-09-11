#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device_record.py
@time: 2017/8/29 21:16
"""

from exts.model_base import ModelBase
from exts.database import db


# 用户的充值记录
class Recharge(ModelBase):
    __tablename__ = 'recharge'

    # 用户ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # 充值金额
    amount = db.Column(db.Integer, nullable=False)

    @classmethod
    def create(cls, user_id, amount):
        recharge = cls(user_id=user_id, amount=amount)
        db.session.add(recharge)
        db.session.commit()
        return recharge

    def __repr__(self):
        return '<Recharge {} {}>'.format(self.username, self.dev_name)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'utime': self.utime.strftime('%Y-%m-%d %H:%I:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%I:%S'),
        }
