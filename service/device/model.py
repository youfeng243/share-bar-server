#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device.py
@time: 2017/8/29 20:59
"""
import json

from sqlalchemy.exc import IntegrityError

from exts.common import log, package_result
from exts.database import db
from exts.model_base import ModelBase


# 设备信息
class Device(ModelBase):
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

        try:
            db.session.add(device)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: device_code = {} address_id = {}".format(
                device_code, address_id))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: device_code = {} address_id = {}".format(
                device_code, address_id))
            log.exception(e)
            return None, False
        return device, True

    # 通过设备编号获取设备信息
    @classmethod
    def get_device_by_code(cls, device_code):
        return cls.query.filter_by(device_code=device_code).first()

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

    # 删除设备需要事务控制
    def delete(self):
        try:
            db.session.delete(self)
            self.address.device_num -= 1 if self.address.device_num >= 1 else 0
            db.session.add(self.address)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            log.error("未知删除错误: {}".format(json.dumps(self.to_dict(), ensure_ascii=False)))
            log.exception(e)
            return False
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'device_code': self.device_code,
            'address': self.address.to_dict(),
            'income': self.income,
            'state': self.state,
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }
