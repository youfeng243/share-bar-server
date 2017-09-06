#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: user.py
@time: 2017/8/29 17:58
"""
from datetime import datetime

from exts.base import Base
from exts.database import db


class User(Base):
    __tablename__ = 'user'

    # 使用状态
    STATE_VALUES = ('unused', 'using')

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 用户名
    username = db.Column(db.String(128), unique=True, index=True, nullable=False)

    # 密码
    password = db.Column(db.String(128), nullable=False)

    # 电话号码
    telephone = db.Column(db.String(64), unique=True, nullable=False)

    # 总充值金额
    total_account = db.Column(db.Integer, nullable=False, default=0)

    # 总的消费金额
    used_account = db.Column(db.Integer, nullable=False, default=0)

    # 当前用户使用状态信息 unused 离线  using 在线
    state = db.Column(db.Enum(*STATE_VALUES), index=True, default='unused')

    # 创建时间
    ctime = db.Column(db.DateTime(), default=datetime.utcnow)

    # 数据更新时间
    utime = db.Column(db.DateTime(), default=datetime.utcnow)

    # 删除用户
    deleted = db.Column(db.Boolean, default=False)

    # 禁止用户 如用户违反规定则停用该用户
    forbid = db.Column(db.Boolean, default=False)

    @classmethod
    def create(cls, username, password, telephone):
        user = cls(
            username=username,
            password=password,
            telephone=telephone)
        db.session.add(user)
        db.session.commit()
        return user

    # 禁止用户
    def forbidden(self):
        self.forbid = True
        self.save()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'telephone': self.telephone,
            'total_account': self.total_account,
            'used_account': self.used_account,
            'state': self.state,
            'ctime': self.ctime,
            'utime': self.utime,
            'forbid': self.forbid,
            'deleted': self.deleted,
        }

    def __repr__(self):
        return '<User {}>'.format(self.username)