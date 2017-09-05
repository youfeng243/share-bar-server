#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device_put_record.py
@time: 2017/8/29 21:26
"""
from datetime import datetime

from exts.database import db


# 设备部署管理 部署记录信息
class Deploy(db.Model):
    __tablename__ = 'deploy'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 设备名称
    device_id = db.Column(db.Integer, index=True)

    # 省份信息
    province = db.Column(db.String(16), nullable=False)

    # 市级信息
    city = db.Column(db.String(64), nullable=False)

    # 区域信息
    area = db.Column(db.String(64), nullable=False)

    # 详细地址信息
    location = db.Column(db.String(128), nullable=False)

    # 生效时间 创建时间
    ctime = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

    # 数据更新时间
    utime = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

    @classmethod
    def create(cls, device_id, province, city, area, location):
        deploy = cls(
            device_id=device_id,
            province=province,
            city=city,
            area=area,
            location=location)
        db.session.add(deploy)
        db.session.commit()
        return deploy

    @classmethod
    def get(cls, a_id):
        return cls.query.get(a_id)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def save(self):
        self.utime = datetime.now()
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'province': self.province,
            'city': self.city,
            'area': self.area,
            'location': self.location,
            'utime': self.utime,
            'ctime': self.ctime,
        }

    def __repr__(self):
        return '<Deploy {}>'.format(self.dev_name)
