#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: user.py
@time: 2017/8/29 17:58
"""

from exts.resource import db
from exts.model_base import ModelBase
from service.recharge.model import Recharge

# 初始化user表前置依赖
__all__ = ["Recharge"]


class User(ModelBase):
    __tablename__ = 'user'

    # 使用状态
    STATUS_VALUES = ('unused', 'using')

    # 用户微信唯一ID
    openid = db.Column(db.String(512), index=True, unique=True, nullable=True)

    # 用户昵称 通过微信端获取
    nick_name = db.Column(db.String(63), default="")

    # 微信头像链接
    head_img_url = db.Column(db.String(256), default="")

    # 电话号码
    mobile = db.Column(db.String(64), unique=True, index=True, nullable=False)

    # 总游戏使用时长  分钟为单位
    total_cost_time = db.Column(db.Integer, nullable=False, default=0)

    # 总充值金额
    total_account = db.Column(db.Integer, nullable=False, default=0)

    # 总的消费金额
    used_account = db.Column(db.Integer, nullable=False, default=0)

    # 总余额，余额不一定是总充值金额 减去 总消费金额，有可能活动获得奖励金额
    balance_account = db.Column(db.Integer, nullable=False, default=0)

    # 当前用户使用状态信息 unused 禁用  using 使用
    state = db.Column(db.Enum(*STATUS_VALUES), index=True, default='using')

    # 删除用户
    deleted = db.Column(db.Boolean, default=False)

    # 改变用户使用状态
    def change_state(self, state):
        if state not in self.STATUS_VALUES:
            return False
        self.state = state
        return self.save()

    def to_dict(self):
        return {
            'id': self.id,
            'nick_name': self.nick_name,
            'head_img_url': self.head_img_url,
            'mobile': self.mobile,
            'total_account': self.total_account,
            'used_account': self.used_account,
            'balance_account': self.balance_account,
            'state': self.state,
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'total_cost_time': self.total_cost_time,
        }

    def __repr__(self):
        return '<User {}>'.format(self.mobile)
