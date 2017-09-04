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

from exts.database import db


class Admin(db.Model):
    __tablename__ = 'admin'

    # 使用状态
    STATE_VALUES = ('unused', 'using')

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 用户名
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # 密码
    password = db.Column(db.String(64), nullable=False)

    # 名称
    name = db.Column(db.String(64), unique=True, nullable=False)

    # 角色 外键 todo 创建外键失败
    role_id = db.Column(db.Integer, nullable=False)
    # role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    # 管理员启动状态 0 未使用 1 正在使用
    state = db.Column(db.Enum(*STATE_VALUES), index=True, default='unused')

    # 管理员创建时间
    ctime = db.Column(db.DateTime(), default=datetime.utcnow)

    # 数据更新时间
    utime = db.Column(db.DateTime(), default=datetime.utcnow)

    @classmethod
    def create(cls, username, password, name, role_id):
        admin = cls(
            username=username,
            password=password,
            name=name,
            role_id=role_id)
        db.session.add(admin)
        db.session.commit()
        return admin

    @classmethod
    def get(cls, a_id):
        return cls.query.get(a_id)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    # 删除数据
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    # 更新下修改时间
    def save(self):
        self.utime = datetime.now()
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return '<Admin {}>'.format(self.addr_id)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'name': self.name,
            'role_id': self.role_id,
            'use_state': self.use_state,
            'utime': self.utime,
            'ctime': self.ctime,
        }
