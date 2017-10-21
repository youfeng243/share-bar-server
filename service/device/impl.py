#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/10/21 11:20
"""
import time

from sqlalchemy.exc import IntegrityError

from exts.common import log, DEFAULT_EXPIRED_DEVICE_HEART
from exts.redis_api import RedisClient
from exts.resource import db, redis_device_client
from service.device.model import Device


class DeviceService(object):
    @staticmethod
    def create(device_code, address_id):
        device = Device(device_code=device_code, address_id=address_id)

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
    @staticmethod
    def get_device_by_code(device_code):
        return Device.query.filter_by(device_code=device_code).first()

    # 保持心跳
    @staticmethod
    def keep_device_heart(device_code):
        # 先获得心跳的主键
        device_heart_key = RedisClient.get_device_heart_key(device_code)

        redis_device_client.setex(device_heart_key, DEFAULT_EXPIRED_DEVICE_HEART, int(time.time()))
