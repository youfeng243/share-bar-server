#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/10/21 11:20
"""
import json
import time
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from exts.common import log, DEFAULT_EXPIRED_DEVICE_HEART, DEFAULT_EXPIRED_DEVICE_STATUS, \
    REDIS_PRE_DEVICE_ALIVE_SYNC_LAST_TIME_KEY, DEFAULT_EXPIRED_DEVICE_ALIVE_SYNC, get_now_time
from exts.redis_api import RedisClient
from exts.resource import db, redis_device_client
from service.device.model import Device


# 设备操作接口
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

    # 获得设备最新存活状态
    @staticmethod
    def get_device_alive_status(device):

        if isinstance(device, basestring):
            device_code = device
        elif isinstance(device, Device):
            device_code = device.device_code
        else:
            log.error("当前设备参数获取存活状态不正确: device = {} type = {}".format(device, type(device)))
            return Device.ALIVE_OFFLINE

        # 先获得心跳的主键
        device_heart_key = RedisClient.get_device_heart_key(device_code)
        last_heart_time = redis_device_client.get(device_heart_key)
        if last_heart_time is None:
            return Device.ALIVE_OFFLINE

        return Device.ALIVE_ONLINE

    # 同步redis中设备状态, 5分钟全量同步一次，防止反复同步性能低下
    @staticmethod
    def sync_device_alive_status():

        # 先获得全体设备最后同步时间
        sync_last_time = redis_device_client.get(REDIS_PRE_DEVICE_ALIVE_SYNC_LAST_TIME_KEY)
        if sync_last_time is not None:
            log.info("当前设备存活状态不需要更新到数据库, 上次同步时间: {}".format(sync_last_time))
            return

        start_time = time.time()

        # 获得全部设备信息
        device_list = Device.get_all()
        for device in device_list:
            # 更新设备存活状态
            device.alive = DeviceService.get_device_alive_status(device.device_code)
            device.utime = datetime.now()
            db.session.add(device)

        if len(device_list) > 0:
            try:
                db.session.commit()
            except Exception as e:
                log.error("提交存储设备信息错误:")
                log.exception(e)

        # 存入最新同步时间
        redis_device_client.setex(REDIS_PRE_DEVICE_ALIVE_SYNC_LAST_TIME_KEY,
                                  DEFAULT_EXPIRED_DEVICE_ALIVE_SYNC,
                                  get_now_time())

        log.info("同步设备数目为: count = {}".format(len(device_list)))
        log.info("同步设备信息花费时间: start_time = {} use time = {} s".format(start_time, time.time() - start_time))

    # 获得设备使用状态
    @staticmethod
    def get_device_status(device):

        '''
        获取设备使用状态
        :param device: basestring or Device 类型
        :return:
        '''

        if isinstance(device, basestring):
            device_code = device
        elif isinstance(device, Device):
            # 如果传入的是设备信息直接返回设备使用状态即可， 缓存和数据库中的设备信息是保持严格一致的，只要写入则同时写入缓存和数据库
            return device.state
        else:
            log.error("当前参数数据类型不正确: device = {} type = {}".format(device, type(device)))
            return None

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

    # 设置设备状态
    @staticmethod
    def set_device_status(device, device_status):
        '''
        :param device: Device 类型
        :param device_status:
        :return:
        '''
        if not isinstance(device, Device):
            log.error("当前设置设备状态传入参数错误: device = {} type = {}".format(
                device, type(device)))
            return

        if device_status not in Device.STATUS_VALUES:
            log.error("当前设置设备状态传入参数错误: device_status = {}".format(device_status))
            return

        device.state = device_status
        device_status_key = RedisClient.get_device_status_key(device.device_code)

        # 存储状态到redis中 状态只保存一天，防止数据被删除 缓存一直存在
        redis_device_client.setex(device_status_key, DEFAULT_EXPIRED_DEVICE_STATUS, device.state)

    # shanchu 设备
    @staticmethod
    def delete_device(device_id):

        device = Device.get(device_id)

        if device is None:
            log.warn("当前需要删除的设备不存在: device_id = {}".format(device_id))
            return False

        # 当前设备在线，且设备正在被用户使用，则不能够删除
        if DeviceService.get_device_alive_status(device) == Device.ALIVE_ONLINE and \
                        DeviceService.get_device_status(device) != Device.STATUE_FREE:
            log.warn("当前设备不处于空闲状态，不能删除: device_id = {}".format(device.id))
            return False

        device_status_key = RedisClient.get_device_status_key(device.device_code)
        if not device.delete():
            log.warn("设备信息删除失败: {}".format(json.dumps(device.to_dict(), ensure_ascii=False)))
            return False

        # 删除缓存信息
        redis_device_client.delete(device_status_key)
        return True
