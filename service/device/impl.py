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

from flask import has_request_context
from flask import request
from sqlalchemy.exc import IntegrityError

from exts.common import log, DEFAULT_EXPIRED_DEVICE_HEART, DEFAULT_EXPIRED_DEVICE_STATUS, \
    REDIS_PRE_DEVICE_ALIVE_SYNC_LAST_TIME_KEY, DEFAULT_EXPIRED_DEVICE_ALIVE_SYNC, get_now_time, fail, HTTP_OK, success, \
    package_result
from exts.redis_api import RedisClient
from exts.resource import db, redis_device_client
from service.address.model import Address
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

    # 根据设备ID 获取设备信息
    @staticmethod
    def get_device_by_id(device_id):
        return Device.get(device_id)

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
            update_info = {
                Device.alive: DeviceService.get_device_alive_status(device.device_code),
                Device.utime: datetime.now()
            }
            Device.query.filter_by(id=device.id).update(update_info)

        # 存入最新同步时间
        redis_device_client.setex(REDIS_PRE_DEVICE_ALIVE_SYNC_LAST_TIME_KEY,
                                  DEFAULT_EXPIRED_DEVICE_ALIVE_SYNC,
                                  get_now_time())

        log.info("同步设备存活状态数目为: count = {}".format(len(device_list)))
        log.info("同步设备存活信息花费时间: start_time = {} use time = {} s".format(start_time, time.time() - start_time))

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

    # 状态转移 这个接口目前只用于 从 维护状态转移到空闲状态
    @staticmethod
    def status_transfer(device_code, from_status, to_status):
        if from_status == to_status:
            return

        device = DeviceService.get_device_by_code(device_code)
        if device is None:
            log.error("当前设备码不正确, 找不到设备: device_code = {}".format(device_code))
            return

        DeviceService.set_device_status(device, to_status)
        log.info("设备状态切换完成: device_code = {} from_status = {} to_status = {}".format(
            device_code, from_status, to_status))

    # 设置设备状态
    @staticmethod
    def set_device_status(device, device_status):
        '''
        :param save: 是否存储
        :param device: Device 类型
        :param device_status:
        :return:
        '''
        if not isinstance(device, Device):
            log.error("当前设置设备状态传入参数错误: device = {} type = {}".format(
                device, type(device)))
            return False

        if device_status not in Device.STATUS_VALUES:
            log.error("当前设置设备状态传入参数错误: device_status = {}".format(device_status))
            return False

        # 先更新数据库，确保数据更新成功
        update_info = {
            Device.state: device_status,
            Device.state_version: device.state_version + 1
        }
        rowcount = Device.query.filter_by(id=device.id, state_version=device.state_version).update(update_info)
        if rowcount <= 0:
            log.error("更新设备状态失败，版本信息已经被修改: id = {} state_version = {} state = {}".format(
                device.id, device.state_version, device_status))
            return False

        device_status_key = RedisClient.get_device_status_key(device.device_code)

        # 存储状态到redis中 状态只保存一天，防止数据被删除 缓存一直存在
        redis_device_client.setex(device_status_key, DEFAULT_EXPIRED_DEVICE_STATUS, device_status)
        log.info("设备状态设置成功: device_id = {} device_code = {} state = {} state_version = {}".format(
            device.id, device.device_code, device_status, device.state_version + 1))
        return True

    # shanchu 设备
    @staticmethod
    def delete_device(device_id):

        device = DeviceService.get_device_by_id(device_id)

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

    @staticmethod
    def find_list(province, city, area,
                  start_time, end_time,
                  state, alive,
                  page, size,
                  filters=None, order_by=None):
        # 条件查询
        total = 0
        query = Device.query

        # 根据省份查询
        if province is not None:
            query = query.join(Address).filter(Address.province == province)
            log.info("当前按省份筛选: province = {}".format(province))

            # 根据城市查询
            if city is not None:
                query = query.filter(Address.city == city)
                log.info("当前按城市筛选: city = {}".format(city))

                # 在有城市的前提下按区域查询
                if area is not None:
                    query = query.filter(Address.area == area)
                    log.info("当前按区域筛选: area = {}".format(area))

        # 增加过滤条件
        if isinstance(filters, list):
            for filter_item in filters:
                query = query.filter(filter_item)

        # 根据使用状态查询
        if state is not None:
            query = query.filter(Device.state == state)

        # 根据存活状态查询
        if alive is not None:
            query = query.filter(Device.alive == alive)

        # 根据时间查询
        if start_time is not None and end_time is not None:
            query = query.filter(Device.ctime.between(start_time, end_time))
        elif start_time is not None:
            query = query.filter(Device.ctime >= start_time)
        elif end_time is not None:
            query = query.filter(Device.ctime <= end_time)

        # 是否需要排序
        if order_by is not None:
            query = query.order_by(order_by)

        pagination = query.paginate(
            page=page,
            per_page=size,
            error_out=False)

        if pagination is None:
            return total, None

        # 获取数据总数目
        return pagination.total, pagination.items

    # 根据条件进行搜索
    @staticmethod
    def search_list():

        if not has_request_context():
            log.warn("上下文异常")
            return fail(HTTP_OK, u"服务器未知!")

        if not request.is_json:
            log.warn("参数错误...")
            return fail(HTTP_OK, u"need application/json!!")

        filters = list()
        page = request.json.get('page')
        size = request.json.get('size')
        province = request.json.get('province')
        city = request.json.get('city')
        area = request.json.get('area')
        start_time_str = request.json.get('start_time')
        end_time_str = request.json.get('end_time')
        state = request.json.get('state')
        alive = request.json.get('alive')

        order_by = request.json.get('order_by')

        # 如果存在状态信息，但是状态错误，则返回错误
        if state is not None:
            if state not in Device.STATUS_VALUES:
                return fail(HTTP_OK, u'状态信息错误!')

        # 判断是否有检测设备状态
        if alive is not None:
            if alive not in Device.ALIVE_VALUES:
                return fail(HTTP_OK, u'存活状态信息错误!')

        if isinstance(start_time_str, basestring) and isinstance(end_time_str, basestring):
            if end_time_str < start_time_str:
                return fail(HTTP_OK,
                            u"时间区间错误: start_time = {} > end_time = {}".format(start_time_str, end_time_str))

        try:
            # 转换为 datetime 类型
            start_time = None
            if isinstance(start_time_str, basestring):
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                log.info("转换后时间: start_time = {} type = {}".format(start_time, type(start_time)))
            else:
                log.info("start_time 不是字符串: {}".format(start_time_str))

            end_time = None
            if isinstance(end_time_str, basestring):
                end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                log.info("转换后时间: end_time = {} type = {}".format(end_time, type(end_time)))
            else:
                log.info("end_time 不是字符串: {}".format(end_time_str))
        except Exception as e:
            log.error("时间格式转换错误: start_time_str = {} end_time_str = {}".format(start_time_str, end_time_str))
            log.exception(e)
            return fail(HTTP_OK, u"时间格式转换错误!")

        if not isinstance(page, int) or \
                not isinstance(size, int):
            log.warn("请求参数错误: page = {} size = {}".format(page, size))
            return fail(HTTP_OK, u"请求参数错误")

            # 请求参数必须为正数
        if page <= 0 or size <= 0:
            msg = "请求参数错误: page = {} size = {}".format(
                page, size)
            log.error(msg)
            return fail(HTTP_OK, msg)

        if size > 50:
            log.info("翻页最大数目只支持50个, 当前size超过50 size = {}!".format(size))
            size = 50
        total, item_list = DeviceService.find_list(province, city, area, start_time,
                                                   end_time, state, alive, page,
                                                   size, filters=filters,
                                                   order_by=order_by)
        if total <= 0 or item_list is None:
            return success(package_result(0, []))
        return success(package_result(total, [item.to_dict() for item in item_list]))
