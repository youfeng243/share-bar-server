#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: mock.py
@time: 2017/10/23 12:20
"""

# 设备信息
from exts.model_base import ModelBase
from exts.resource import db


class Maintain(ModelBase):
    # 所有地点
    ALL_ADDRESS = -1

    __tablename__ = 'maintain'

    # 使用状态
    STATUS_VALUES = ('unused', 'using')

    # 用户名
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # 密码
    hashed_password = db.Column(db.String(256), nullable=False)

    # 姓名
    name = db.Column(db.String(64), nullable=False)

    # 管理员启用状态 using 启用 unused 停用
    state = db.Column(db.Enum(*STATUS_VALUES), index=True, default='using')

    # 管理地址ID
    address_id = db.Column(db.Integer, default=ALL_ADDRESS)
