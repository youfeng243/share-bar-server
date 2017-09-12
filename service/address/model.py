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

from sqlalchemy.exc import IntegrityError

from exts.common import log, package_result
from exts.database import db
from exts.model_base import ModelBase


# 投放管理
class Address(ModelBase):
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
    device_query = db.relationship('Device', backref='address', lazy='dynamic')

    # 生效时间 创建时间
    ctime = db.Column(db.DateTime, index=True, default=datetime.now(), nullable=False)

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
        try:
            db.session.add(address)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: province = {} city = {} area = {} location = {}".format(
                province, city, area, location))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: province = {} city = {} area = {} location = {}".format(
                province, city, area, location))
            log.exception(e)
            return None, False
        return address, True

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

    # 根据城市名称与区域名称查询数据信息
    @classmethod
    def find_address_by_city_and_area(cls, city, area, page, size=10):
        result_list = []
        query = cls.query

        # 先过滤城市信息
        query = query.filter(cls.city == city)

        # 再过滤区域信息
        if area is not None:
            query = query.filter(cls.area == area)

        # 获得数目信息
        total = query.count()

        pagination = query.paginate(
            page=page,
            per_page=size,
            error_out=False,
        )

        if pagination is None:
            log.error("地址信息查询异常...")
            return package_result(total, result_list)

        item_list = pagination.items
        if not isinstance(item_list, list):
            log.error("地址信息查询异常...")
            return package_result(total, result_list)

        return package_result(total, [item.to_dict() for item in item_list])

    # 根据时间查询地址信息
    @classmethod
    def find_address_by_time(cls, start_time, end_time, page, size=10):
        result_list = []
        query = cls.query

        # 根据创建时间范围进行过滤
        query = query.filter(cls.ctime.between(start_time, end_time))

        # 获取数据总数目
        total = query.count()

        # 根据时间进行排序
        query = query.order_by(cls.ctime)

        pagination = query.paginate(
            page=page,
            per_page=size,
            error_out=False,
        )

        if pagination is None:
            log.error("时间信息查询异常...")
            return package_result(total, result_list)

        item_list = pagination.items
        if not isinstance(item_list, list):
            log.error("时间信息查询异常...")
            return package_result(total, result_list)

        return package_result(total, [item.to_dict() for item in item_list])

    # 获得所有列表信息
    @classmethod
    def get_address_list(cls, page, size=10):
        result_list = []

        # 获取数据总数目
        total = cls.query.count()

        item_paginate = cls.query.paginate(page=page, per_page=size, error_out=False)
        if item_paginate is None:
            log.warn("地址信息分页查询失败: page = {} size = {}".format(page, size))
            return package_result(total, result_list)

        item_list = item_paginate.items
        if item_list is None:
            log.warn("地址信息分页查询失败: page = {} size = {}".format(page, size))
            return package_result(total, result_list)

        return package_result(total, [item.to_dict() for item in item_list])

    # 增加设备数目
    def add_device_num(self, device_num):
        self.device_num += device_num
        return self.save()

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
