#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: role.py
@time: 2017/8/30 09:06
"""

from exts.model_base import ModelBase
from exts.database import db


# 管理员角色管理
class Role(ModelBase):
    __tablename__ = 'role'

    # 超级管理员
    SUPER_ADMIN = u"superadmin"

    # 角色名称
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # 反向指向用户信息
    admin_query = db.relationship('Admin', backref='role', lazy='dynamic')

    # todo 角色权限 这里需要角色的权限管理，目前没想好先预留

    @classmethod
    def create(cls, name):
        role = cls(
            name=name)
        db.session.add(role)
        db.session.commit()
        return role

    @classmethod
    def get_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    def __repr__(self):
        return '<Role {}>'.format(self.role_name)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'utime': self.utime.strftime('%Y-%m-%d %H:%I:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%I:%S'),
        }
