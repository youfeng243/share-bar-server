#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device_record.py
@time: 2017/8/29 21:16
"""
from sqlalchemy.exc import IntegrityError

from exts.common import log
from exts.database import db
from exts.model_base import ModelBase


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

        try:
            db.session.add(recharge)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: user_id = {} amount = {}".format(
                user_id, amount))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: user_id = {} amount = {}".format(
                user_id, amount))
            log.exception(e)
            return None, False
        return recharge, True

    def __repr__(self):
        return '<Recharge {} {}>'.format(self.username, self.dev_name)

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict(),
            'amount': self.amount,
            'utime': self.utime.strftime('%Y-%m-%d %H:%I:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%I:%S'),
        }
