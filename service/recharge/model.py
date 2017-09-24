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

from sqlalchemy.exc import IntegrityError

from exts.common import log
from exts.database import db
from exts.model_base import ModelBase
from service.user.model import User


class Recharge(ModelBase):
    __tablename__ = 'recharge'

    # 用户ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # 充值流水账号 每一次充值带时间戳的唯一ID
    transaction_id = db.Column(db.String(64), index=True, nullable=False)

    # 充值金额
    amount = db.Column(db.Integer, index=True, nullable=False)

    # 付款时间
    pay_time = db.Column(db.DateTime, default=datetime.now())

    @classmethod
    def create(cls, user_id, amount, transaction_id, pay_time):
        recharge = cls(user_id=user_id,
                       amount=amount,
                       transaction_id=transaction_id,
                       pay_time=pay_time)

        # 账户总额增加
        user = User.get(user_id)
        if user is None:
            log.warn("当前充值用户信息不存在: user_id = {}".format(user_id))
            return None, False

        try:
            user.balance_account += amount
            user.total_account += amount
            user.utime = datetime.now()
            db.session.add(user)
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
            'transaction_id': self.transaction_id,
            'pay_time': self.pay_time.strftime('%Y-%m-%d %H:%M:%S'),
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }
