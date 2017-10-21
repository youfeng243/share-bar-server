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

from exts.common import log, DEFAULT_EXPIRED_DEVICE_HEART, DEFAULT_EXPIRED_DEVICE_STATUS
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

    # 获得设备使用状态
    @staticmethod
    def get_device_status(device_code):

        # 先判断是否在缓存中
        device_status_key = RedisClient.get_device_status_key(device_code)

        device_status = redis_device_client.get(device_status_key)
        if device_status is not None:
            return device_status

        # 没有从缓存中找到设备状态 则去数据库中找
        device = DeviceService.get_device_by_code(device_code)
        if device is None:
            log.error("当前设备码没有从缓存中找到，也不存在于数据库中: device_code = {}".format(device_code))
            return None

        # 存储状态到redis中 状态只保存一天，防止数据被删除 缓存一直存在
        redis_device_client.setex(device_status_key, DEFAULT_EXPIRED_DEVICE_STATUS, device.state)

        log.info("当前设备状态从数据库中加载, 缓存到redis中: device_code = {}".format(device_code))
        return device.state
