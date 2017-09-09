#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device.py
@time: 2017/8/29 20:59
"""

from exts.base import Base
from exts.common import log, package_result
from exts.database import db


# 设备信息
class Device(Base):
    __tablename__ = 'device'

    # 使用状态
    STATE_VALUES = ('free', 'busy', 'offline')

    # 设备机器码
    device_code = db.Column(db.String(128), unique=True, index=True)

    # 投放ID
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))

    # 部署记录
    deploy_query = db.relationship('Deploy', backref='device', lazy='dynamic')

    # 设备收入
    income = db.Column(db.Integer, nullable=False, default=0)

    # 设备当前使用状态 free 空闲 busy 忙碌  offline 离线
    state = db.Column(db.Enum(*STATE_VALUES), nullable=False, index=True, default='free')

    @classmethod
    def create(cls, device_code, address_id):
        device = cls(device_code=device_code, address_id=address_id)
        db.session.add(device)
        db.session.commit()
        return device

    # 通过设备编号获取设备信息
    @classmethod
    def get_device_by_code(cls, device_code):
        return cls.query.filter_by(device_code=device_code).first()

    # 分页获取地址信息
    @classmethod
    def get_device_list(cls, page, size=10):

        result_list = []

        # 获取数据总数目
        total = cls.query.count()

        item_paginate = cls.query.paginate(page=page, per_page=size, error_out=False)
        if item_paginate is None:
            log.warn("设备信息分页查询失败: page = {} size = {}".format(page, size))
            return package_result(total, result_list)

        item_list = item_paginate.items
        if item_list is None:
            log.warn("设备信息分页查询失败: page = {} size = {}".format(page, size))
            return package_result(total, result_list)

        # 还需要获取地址信息
        for item in item_list:
            result = item.to_dict()
            result.pop("address_id")
            result['address'] = item.address.to_dict()
            result_list.append(result)

        return package_result(total, result_list)

    def __repr__(self):
        return '<Device {}>'.format(self.name)

    # 获得部署列表
    def get_deploy_list(self, page, size):
        result_list = list()

        # 先获取部署总数信息
        total = self.deploy_query.count()

        # 获取部署信息列表
        item_paginate = self.deploy_query.paginate(page=page, per_page=size, error_out=False)
        if item_paginate is None:
            log.warn("获取部署信息翻页查询失败: device = {} page = {} size = {}".format(self.id, page, size))
            return package_result(total, result_list)

        item_list = item_paginate.items
        if item_list is None:
            log.warn("部署信息分页查询失败: device = {} page = {} size = {}".format(self.id, page, size))
            return package_result(total, result_list)

        return package_result(total, [item.to_dict() for item in item_list])

    def to_dict(self):
        return {
            'id': self.id,
            'device_code': self.device_code,
            'address_id': self.address_id,
            'income': self.income,
            'state': self.state,
            'utime': self.utime.strftime('%Y-%m-%d %H:%I:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%I:%S'),
        }
