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
from service.recharge.model import Recharge

# 初始化user表前置依赖
__all__ = ["Recharge"]


class User(ModelBase):
    __tablename__ = 'user'

    # 使用状态
    STATE_VALUES = ('unused', 'using')

    # 用户微信唯一ID
    openid = db.Column(db.String(512), index=True, nullable=True)

    # 用户昵称 通过微信端获取
    nike_name = db.Column(db.String(63), default="")

    # 微信头像链接
    head_img_url = db.Column(db.String(256), default="")

    # 电话号码
    mobile = db.Column(db.String(64), unique=True, index=True, nullable=False)

    # 总充值金额
    total_account = db.Column(db.Integer, nullable=False, default=0)

    # 总的消费金额
    used_account = db.Column(db.Integer, nullable=False, default=0)

    # 总余额，余额不一定是总充值金额 减去 总消费金额，有可能活动获得奖励金额
    balance_account = db.Column(db.Integer, nullable=False, default=0)

    # 当前用户使用状态信息 unused 禁用  using 使用
    state = db.Column(db.Enum(*STATE_VALUES), index=True, default='using')

    # 反向指向充值列表信息
    recharge_query = db.relationship('Recharge', backref='user', lazy='dynamic')

    # 删除用户
    deleted = db.Column(db.Boolean, default=False)

    @classmethod
    def create(cls, mobile, openid, nike_name="", head_img_url=""):
        user = cls(mobile=mobile,
                   openid=openid,
                   nike_name=nike_name,
                   head_img_url=head_img_url)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: mobile = {}".format(mobile))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: mobile = {}".format(mobile))
            log.exception(e)
            return None, False
        return user, True

    # 根据微信ID 获取用户信息
    @classmethod
    def get_by_openid(cls, openid):
        return cls.query.filter_by(openid=openid).first()

    # 根据手机号码查找用户信息
    @classmethod
    def get_user_by_phone(cls, phone):
        return cls.query.filter_by(mobile=phone).first()

    # 改变用户使用状态
    def change_state(self, state):
        if state not in self.STATE_VALUES:
            return False
        self.state = state
        return self.save()

    def to_dict(self):
        return {
            'id': self.id,
            'nike_name': self.nike_name,
            'mobile': self.mobile,
            'total_account': self.total_account,
            'used_account': self.used_account,
            'balance_account': self.balance_account,
            'state': self.state,
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def __repr__(self):
        return '<User {}>'.format(self.mobile)
