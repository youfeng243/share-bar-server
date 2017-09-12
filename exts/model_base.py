#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: common.py
@time: 2017/8/28 20:58
"""
import json
from datetime import datetime

from exts.common import log
from exts.database import db


class ModelBase(db.Model):
    __abstract__ = True

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 生效时间 创建时间
    ctime = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    # 数据更新时间
    utime = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    def delete(self):
        try:
            if hasattr(self, 'deleted'):
                self.deleted = True
                db.session.add(self)
            else:
                db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            log.error("未知删除错误: {}".format(json.dumps(self.to_dict(), ensure_ascii=False)))
            log.exception(e)
            return False
        return True

    @classmethod
    def get(cls, a_id):
        return cls.query.get(a_id)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    def save(self):
        self.utime = datetime.now()

        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            log.error("未知存储错误: {}".format(json.dumps(self.to_dict(), ensure_ascii=False)))
            log.exception(e)
            return False
        return True

    # 字典转换接口 必须实现
    def to_dict(self):
        raise NotImplementedError
