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

from exts.base import Base
from exts.database import db


# 用户的充值记录
class Recharge(Base):
    __tablename__ = 'recharge'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 用户ID
    user_id = db.Column(db.Integer, index=True, nullable=False)

    # 充值金额
    amount = db.Column(db.Integer, nullable=False)

    # 创建时间
    ctime = db.Column(db.DateTime(), default=datetime.utcnow)

    # 数据更新时间
    utime = db.Column(db.DateTime(), default=datetime.utcnow)

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
            'utime': self.utime,
            'ctime': self.ctime,
        }