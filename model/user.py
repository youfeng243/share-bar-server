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


# 用户信息
from exts.database import db


class User(db.Model):
    __tablename__ = 'users'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 用户名
    username = db.Column(db.String(128), unique=True, index=True, nullable=False)

    # 密码
    password = db.Column(db.String(128), nullable=False)

    # 电话号码
    telephone = db.Column(db.String(64), unique=True, nullable=False)

    # 注册时间
    register_time = db.Column(db.DateTime(), nullable=False)

    # 总充值金额
    total_account = db.Column(db.Integer, nullable=False)

    # 总的消费金额
    used_account = db.Column(db.Integer, nullable=False)

    # 当前用户使用状态信息 0 离线  1 在线
    use_state = db.Column(db.Integer, nullable=False, index=True)

    # 数据被创建的时间
    # in_time = db.Column(db.DateTime(), nullable=False)

    # 数据更新时间
    update_time = db.Column(db.DateTime(), nullable=False)

    def __init__(self, username, password, telephone, total_account, used_account, use_state):
        self.username = username
        self.password = password
        self.telephone = telephone
        self.total_account = total_account
        self.used_account = used_account
        self.use_state = use_state
        self.register_time = self.update_time = datetime.now()

    # 更新数据时间
    def update(self):
        self.update_time = datetime.now()

    def __repr__(self):
        return '<User {}>'.format(self.username)


db.create_all()
