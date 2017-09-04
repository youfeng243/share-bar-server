#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: model.py
@time: 2017/9/2 00:10
"""
from datetime import datetime

from exts.database import db


class Address(db.Model):
    __tablename__ = 'address'

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 省份信息
    province = db.Column(db.String(16), nullable=False)

    # 市级信息
    city = db.Column(db.String(64), nullable=False)

    # 区域信息
    area = db.Column(db.String(64), nullable=False)

    # 详细地址信息
    location = db.Column(db.String(128), nullable=False)

    # 统计设备数目
    device_num = db.Column(db.Integer, nullable=False)

    # 生效时间 创建时间
    ctime = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

    # 数据更新时间
    utime = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

    # 创建联合索引
    __table_args__ = (
        db.UniqueConstraint('province', 'city', 'area', 'location', name='location_index'),
        db.Index('location_index'),
    )

    def __repr__(self):
        return '<Address {}>'.format(self.id)

    @classmethod
    def create(cls, province, city, area, location, device_num):
        address = Address(
            province=province,
            city=city,
            area=area,
            location=location, device_num=device_num)
        db.session.add(address)
        db.session.commit()
        return address

    # 查找是否有相同地址
    @classmethod
    def find_address(cls, province, city, area, location):
        return cls.query.filter_by(province=province, city=city, area=area, location=location).first()

    @classmethod
    def get(cls, addr_id):
        return cls.query.get(addr_id)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def save(self):
        db.session.add(self)
        db.session.commit()

    # 增加设备数目
    def add_device_num(self, device_num):
        self.device_num += device_num
        self.save()

    def to_dict(self):
        return {
            'id': self.id,
            'province': self.province,
            'city': self.city,
            'area': self.area,
            'location': self.location,
            'device_num': self.device_num,
            'utime': self.utime,
            'ctime': self.ctime,
        }
