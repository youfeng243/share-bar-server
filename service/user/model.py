#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: user.py
@time: 2017/8/29 17:58
"""
from sqlalchemy.exc import IntegrityError

from exts.common import log
from exts.database import db
from exts.model_base import ModelBase


class User(ModelBase):
    __tablename__ = 'user'

    # 使用状态
    STATE_VALUES = ('unused', 'using')

    # 电话号码
    telephone = db.Column(db.String(64), unique=True, nullable=False)

    # 总充值金额
    total_account = db.Column(db.Integer, nullable=False, default=0)

    # 总的消费金额
    used_account = db.Column(db.Integer, nullable=False, default=0)

    # 总余额，余额不一定是总充值金额 减去 总消费金额，有可能活动获得奖励金额
    balance_account = db.Column(db.Integer, nullable=False, default=0)

    # 当前用户使用状态信息 unused 离线  using 在线
    state = db.Column(db.Enum(*STATE_VALUES), index=True, default='unused')

    # 反向指向充值列表信息
    recharge_query = db.relationship('Recharge', backref='user', lazy='dynamic')

    # 删除用户
    deleted = db.Column(db.Boolean, default=False)

    @classmethod
    def create(cls, telephone):
        user = cls(telephone=telephone)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: telephone = {}".format(telephone))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: telephone = {}".format(telephone))
            log.exception(e)
            return None, False
        return user, True

    # 改变用户使用状态
    def change_state(self, state):
        if state not in self.STATE_VALUES:
            return False
        self.state = state
        return self.save()

    def to_dict(self):
        return {
            'id': self.id,
            'telephone': self.telephone,
            'total_account': self.total_account,
            'used_account': self.used_account,
            'balance_account': self.balance_account,
            'state': self.state,
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def __repr__(self):
        return '<User {}>'.format(self.telephone)
