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
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from exts.common import log, package_result
from exts.database import db
from exts.model_base import ModelBase


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
class Admin(UserMixin, ModelBase):
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

        try:
            db.session.add(admin)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: username = {} name = {} role_id = {}".format(
                username, name, role_id))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: username = {} name = {} role_id = {}".format(
                username, name, role_id))
            log.exception(e)
            return None, False
        return admin, True

    # 获得管理员列表信息
    @classmethod
    def get_admin_list(cls, page, size=10):

        result_list = []

        total = cls.query.count()

        item_paginate = cls.query.paginate(page=page, per_page=size, error_out=False)
        if item_paginate is None:
            log.warn("管理员信息分页查询失败: page = {} size = {}".format(page, size))
            return package_result(total, result_list)

        item_list = item_paginate.items
        if item_list is None:
            log.warn("管理员信息分页查询失败: page = {} size = {}".format(page, size))
            return package_result(total, result_list)

        return package_result(total, [item.to_dict() for item in item_list])

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
            'role': self.role.to_dict(),
            'state': self.state,
            'utime': self.utime.strftime('%Y-%m-%d %H:%I:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%I:%S'),
        }
