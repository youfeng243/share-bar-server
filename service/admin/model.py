#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: admin_manage.py
@time: 2017/8/30 09:10
"""

from flask_login import UserMixin
from flask_sqlalchemy import BaseQuery
from werkzeug.security import generate_password_hash, check_password_hash

from exts.base import Base
from exts.database import db


# 管理员查询类
class AdminQuery(BaseQuery):
    def _join(self, keys, outerjoin, create_aliases, from_joinpoint):
        pass

    def authenticate(self, username, raw_password):
        admin = self.filter(Admin.username == username).first()
        if admin and admin.verify_password(raw_password):
            return admin
        return None


# 管理员信息
class Admin(UserMixin, Base):
    __tablename__ = 'admin'

    # 接管查询类
    query_class = AdminQuery

    # 使用状态
    STATE_VALUES = ('unused', 'using')

    # 用户名
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # 密码
    hashed_password = db.Column(db.String(256), nullable=False)

    # 姓名 todo 同一个人可以是多种管理员？ 待与PM确认。。
    name = db.Column(db.String(64), nullable=False)

    # 角色 外键 todo 创建外键失败
    # role_id = db.Column(db.Integer, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    # 管理员启用状态 using 启用 unused 停用
    state = db.Column(db.Enum(*STATE_VALUES), index=True, default='using')

    @classmethod
    def create(cls, username, password, name, role_id):
        admin = cls(
            username=username,
            name=name,
            role_id=role_id)
        admin.password = password
        db.session.add(admin)
        db.session.commit()
        return admin

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    # 是否启用状态
    def is_active(self):
        return self.state == 'using'

    @property
    def password(self):  # 设置属性不可读.
        raise AttributeError("Password is not a readable attribute.")

    @password.setter
    def password(self, password):  # 写入密码
        self.hashed_password = generate_password_hash(password)

    def verify_password(self, password):  # 认证密码
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return '<Admin {}>'.format(self.addr_id)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'role_id': self.role_id,
            'state': self.state,
            'utime': self.utime.strftime('%Y-%m-%d %H:%I:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%I:%S'),
        }
