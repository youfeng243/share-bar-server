#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: common.py
@time: 2017/8/28 20:58
"""
from datetime import datetime

from exts.database import db


class Base(db.Model):
    __abstract__ = True

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 生效时间 创建时间
    ctime = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    # 数据更新时间
    utime = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    def delete(self):
        if hasattr(self, 'deleted'):
            self.deleted = True
            db.session.add(self)
        else:
            db.session.delete(self)

        db.session.commit()

    @classmethod
    def get(cls, a_id):
        return cls.query.get(a_id)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    def save(self):
        self.utime = datetime.now()
        db.session.add(self)
        db.session.commit()
