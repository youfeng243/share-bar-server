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

from exts.base import Base
from exts.common import log
from exts.database import db


# 投放管理
class Address(Base):
    __tablename__ = 'address'

    # 省份信息
    province = db.Column(db.String(16), nullable=False)

    # 市级信息
    city = db.Column(db.String(64), index=True, nullable=False)

    # 区域信息
    area = db.Column(db.String(64), index=True, nullable=False)

    # 详细地址信息
    location = db.Column(db.String(128), index=True, nullable=False)

    # 统计设备数目
    device_num = db.Column(db.Integer, nullable=False)

    # 反向指向设备列表信息
    device_list = db.relationship('Device', backref='address', lazy='dynamic')

    # 生效时间 创建时间
    ctime = db.Column(db.DateTime(), index=True, default=datetime.utcnow, nullable=False)

    # 创建联合索引
    __table_args__ = (
        # 第一句与第二句是同义的，但是第二句需要多加一个参数index=True， UniqueConstraint 唯一性索引创建方式
        # db.UniqueConstraint('province', 'city', 'area', 'location', name='location_index'),
        db.Index('location_index_key', 'province', 'city', 'area', 'location', unique=True),
    )

    def __repr__(self):
        return '<Address {}>'.format(self.id)

    @classmethod
    def create(cls, province, city, area, location, device_num=1):
        address = cls(province=province,
                      city=city,
                      area=area,
                      location=location,
                      device_num=device_num)
        db.session.add(address)
        db.session.commit()
        return address

    # 查找是否有相同地址
    @classmethod
    def find_address(cls, province, city, area, location):
        return cls.query.filter_by(province=province, city=city, area=area, location=location).first()

    # 通过详细地址进行查询
    @classmethod
    def find_address_by_location(cls, location):
        result_list = []
        item_list = cls.query.filter_by(location=location)
        if item_list is None:
            return result_list

        return [item.to_dict() for item in item_list]

    # 获得所有列表信息
    @classmethod
    def get_address_list(cls, page, size=10):
        result_list = []

        item_paginate = cls.query.paginate(page=page, per_page=size, error_out=False)
        if item_paginate is None:
            log.warn("地址信息分页查询失败: page = {} size = {}".format(page, size))
            return result_list

        item_list = item_paginate.items
        if item_list is None:
            log.warn("地址信息分页查询失败: page = {} size = {}".format(page, size))
            return result_list

        return [item.to_dict() for item in item_list]

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
            'utime': self.utime.strftime('%Y-%m-%d %H:%I:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%I:%S'),
        }
