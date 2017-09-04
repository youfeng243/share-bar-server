#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: admin_manage.py
@time: 2017/8/30 09:10
"""
from datetime import datetime

from common import db


# 投放地址管理 需要写入统计设备信息
class AdminManage(db.Model):
    __tablename__ = 'admin_manage'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 用户名
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # 密码
    password = db.Column(db.String(64), nullable=False)

    # 名称
    name = db.Column(db.String(64), nullable=False)

    # 角色 外键 todo 创建外键失败
    role_id = db.Column(db.Integer, nullable=False)

    # 管理员启动状态 0 未使用 1 正在使用
    use_state = db.Column(db.Integer, nullable=False, index=True)

    # 管理员创建时间
    in_time = db.Column(db.DateTime(), nullable=False)

    # 数据更新时间
    update_time = db.Column(db.DateTime(), nullable=False)

    def __init__(self, username, password, name, role_id, use_state):
        self.username = username
        self.password = password
        self.name = name
        self.role_id = role_id
        self.use_state = use_state
        self.update_time = self.in_time = datetime.now()

    # 更新数据时间
    def update(self):
        self.update_time = datetime.now()

    def __repr__(self):
        return '<AdminManage {}>'.format(self.addr_id)


# db.drop_all()
db.create_all()
