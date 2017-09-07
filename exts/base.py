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

    def delete(self):
        if hasattr(self, 'deleted'):
            self.deleted = True
            db.session.add(self)
        else:
            db.session.delete(self)

        db.session.commit()

    @classmethod
    def get(cls, addr_id):
        return cls.query.get(addr_id)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    def save(self):
        self.utime = datetime.now()
        db.session.add(self)
        db.session.commit()
