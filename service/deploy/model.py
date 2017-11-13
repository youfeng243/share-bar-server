#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device_put_record.py
@time: 2017/8/29 21:26
"""
from sqlalchemy.exc import IntegrityError

from exts.common import log
from exts.model_base import ModelBase
from exts.resource import db
from service.device.impl import DeviceService


class Deploy(ModelBase):
    __tablename__ = 'deploy'

    # 设备名称
    device_id = db.Column(db.Integer, index=True, nullable=False)

    # 省份信息
    province = db.Column(db.String(16), nullable=False)

    # 市级信息
    city = db.Column(db.String(64), nullable=False)

    # 区域信息
    area = db.Column(db.String(64), nullable=False)

    # 详细地址信息
    location = db.Column(db.String(128), nullable=False)

    #
    # # 创建联合索引
    # __table_args__ = (
    #     # 第一句与第二句是同义的，但是第二句需要多加一个参数index=True， UniqueConstraint 唯一性索引创建方式
    #     # db.UniqueConstraint('province', 'city', 'area', 'location', name='location_index'),
    #     db.Index('deploy_index_key', 'device_id', 'province', 'city', 'area', 'location'),
    # )

    @classmethod
    def create(cls, device_id, province, city, area, location):
        deploy = cls(
            device_id=device_id,
            province=province,
            city=city,
            area=area,
            location=location)

        try:
            db.session.add(deploy)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: device_id = {} province = {} city = {} area = {} location = {}".format(
                device_id, province, city, area, location))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: device_id = {} province = {} city = {} area = {} location = {}".format(
                device_id, province, city, area, location))
            log.exception(e)
            return None, False

        return deploy, True

    def to_dict(self):
        device = DeviceService.get_device_by_id(self.device_id)
        if device is None:
            device_dict = {}
        else:
            device_dict = device.to_dict()

        return {
            'id': self.id,
            'device': device_dict,
            'province': self.province,
            'city': self.city,
            'area': self.area,
            'location': self.location,
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def __repr__(self):
        return '<Deploy {}>'.format(self.dev_name)
