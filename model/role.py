#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: role.py
@time: 2017/8/30 09:06
"""
from datetime import datetime


# 角色管理 主要用于管理管理员
from exts.database import db


class Role(db.Model):
    __tablename__ = 'roles'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 角色名称
    role_name = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # todo 角色权限 这里需要角色的权限管理，目前没想好先预留

    # 数据被创建的时间
    in_time = db.Column(db.DateTime(), nullable=False)

    # 数据更新时间
    update_time = db.Column(db.DateTime(), nullable=False)

    # 管理员表
    # admin = db.relationship('admin_manage', backref='role_id')

    def __init__(self, role_name):
        self.role_name = role_name
        self.in_time = self.update_time = datetime.now()

    # 更新数据时间
    def update(self):
        self.update_time = datetime.now()

    def __repr__(self):
        return '<Role {}>'.format(self.role_name)


# db.drop_all()
db.create_all()
