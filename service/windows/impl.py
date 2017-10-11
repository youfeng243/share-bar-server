#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/9/26 16:22
"""
import json
from datetime import datetime

from exts.charge_manage import Lock
from exts.common import log, fail, HTTP_OK, success, cal_cost_time
from exts.database import redis, db
from exts.redis_dao import get_record_key, get_device_key, get_device_code_key, get_keep_alive_key
from exts.redis_dao import get_user_key
from service.device.model import Device
from service.use_record.model import UseRecord
from service.user.model import User


class WindowsService(object):
    @staticmethod
    def cal_offline(user_id, device_id, record_id, charge_mode):
        try:
            # 获得用户信息
            user = User.get(user_id)

            # 获得设备信息
            device = Device.get(device_id)

            # 获得试用记录
            record = UseRecord.get(record_id)

            # 记录下机时间
            record.end_time = datetime.now()

            # 设置设备为空闲状态
            device.state = Device.STATE_FREE

            log.info("本次上机时间: {} 下机时间: {} 使用记录ID: {} 当前设备: {}".format(
                record.ctime.strftime('%Y-%m-%d %H:%M:%S'),
                record.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                record_id,
                device.device_code))

            # 计算花费时间
            seconds = (record.end_time - record.ctime).seconds
            # # 如果大于半分钟就以一分钟的价格扣钱
            # if 30 <= seconds < 60:
            #     seconds = 60

            record.cost_time = cal_cost_time(seconds)
            log.info("本次上机花费的时间: user_id = {} device_id = {} cost_time = {}".format(
                user_id, device_id, record.cost_time))

            # 计算花费金钱
            record.cost_money = record.cost_time * charge_mode
            log.info("本次上机花费的金钱: user_id = {} device_id = {} cost_money = {}".format(
                user_id, device_id, record.cost_money))

            # 计算设备获得的金钱数目
            device.income += record.cost_money

            # 计算用户花费的钱
            user.balance_account -= record.cost_money
            if user.balance_account < 0:
                user.balance_account = 0
            log.info("上机后用户所剩余额: user_id = {} balance_account = {}".format(user_id, user.balance_account))
            user.used_account += record.cost_money

            db.session.add(user)
            db.session.add(device)
            db.session.add(record)
            db.session.commit()
        except Exception as e:
            log.error("未知错误: user_id = {} device_id = {} record_id = {}".format(user_id, device_id, record_id))
            log.exception(e)
            db.session.rollback()
            return False

        return True

    # 上线操作
    @staticmethod
    def do_online(user, device):
        log.info("用户还未上机可以进行上机: user_id = {} device_id = {}".format(user.id, device.id))
        record, is_success = UseRecord.create(user.id,
                                              device.id,
                                              device.address.province,
                                              device.address.city,
                                              device.address.area,
                                              device.address.location)
        if not is_success:
            return False

        # 判断是否已经在redis中进行记录
        record_key = get_record_key(user.id, device.id)
        # 获得用户上线key
        user_key = get_user_key(user.id)
        # 获得设备上线key
        device_key = get_device_key(device.id)
        # 获得当前设备token
        device_code_key = get_device_code_key(device.device_code)

        # 获得keep_alive_key 更新最新存活时间
        keep_alive_key = get_keep_alive_key(record_key)

        log.info("当前上机时间: user_id:{} device_id:{} record_id:{} ctime:{}".format(
            user.id, device.id, record.id, record.ctime.strftime('%Y-%m-%d %H:%M:%S')))

        # 获得计费结构体
        charging = record.to_charging()
        # 得到计费方式
        charging['charge_mode'] = device.charge_mode
        # 得到当前用户总额
        charging['balance_account'] = user.balance_account
        # 填充设备机器码
        charging['device_code'] = device.device_code

        # charging = {
        #     'id': self.id,
        #     'user_id': self.user_id,
        #     'device_id': self.device_id,
        #     # 花费金额数目
        #     'cost_money': self.cost_money,
        #     # 上机时间
        #     'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        #     # 更新时间，主要用户同步计费
        #     'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
        #     # 已经上机时间
        #     'cost_time': self.cost_time,
        #     # 计费方式 目前默认 5分钱/分钟
        #     'charge_mode': 5,
        #     # 当前用户余额
        #     'balance_account': 10000,
        #     # 设备机器码
        #     'device_code': 'xx-xx-xx-xx-xx-xx',
        # }

        charge_str = json.dumps(charging)

        # 操作redis 需要加锁
        lock = Lock(user_key, redis)
        try:
            lock.acquire()

            # 开始上线 把上线信息存储redis
            redis.set(record_key, charge_str)
            redis.set(user_key, record_key)
            redis.set(device_key, record_key)
            # 根据设备机器码获得记录token
            redis.set(device_code_key, record_key)
            # 设置最新存活时间
            import time
            redis.set(keep_alive_key, int(time.time()))

            # 设置设备当前使用状态
            device.state = Device.STATE_BUSY
            device.save()
        finally:
            lock.release()

        return True

    @staticmethod
    def do_offline(charging):

        # offline_lock_key = None
        lock = None
        try:
            if charging is None:
                log.error("charging is None 下机异常!!")
                return fail(HTTP_OK, u"下机异常!")

            charge_dict = json.loads(charging)
            record_id = charge_dict.get('id')
            user_id = charge_dict.get('user_id')
            device_id = charge_dict.get('device_id')
            charge_mode = charge_dict.get('charge_mode')
            device_code = charge_dict.get('device_code')
            log.info("当前下线信息: user_id = {} device_id = {} charge_mode = {} device_code = {}".format(
                user_id, device_id, charge_mode, device_code))

            user_key = get_user_key(user_id)

            #  todo 下机需要加锁
            lock = Lock(user_key, redis)

            log.info("开始加锁下机: user_key = {}".format(user_key))

            # 加锁下机
            lock.acquire()

            # 判断是否已经在redis中进行记录
            record_key = get_record_key(user_id, device_id)
            if redis.get(record_key) is None:
                log.warn("当前用户或者设备已经下机: user_id = {} device_id = {}".format(user_id, device_id))
                return success({'status': 1, 'msg': 'logout successed!'})

            # # 获得下机锁
            # offline_lock_key = get_offline_lock_key(record_key)
            #
            # if redis.get(offline_lock_key) is not None:
            #     log.warn("当前已经在下机，其他下机请求被忽略: record_key = {}".format(record_key))
            #     return success({'status': 1, 'msg': 'logout successed!'})
            #
            # # 加上下机锁
            # redis.set(offline_lock_key, 'lock')
            # log.info("当前获得下机锁: {}".format(offline_lock_key))

            # 结账下机
            if not WindowsService.cal_offline(user_id=user_id,
                                              device_id=device_id,
                                              record_id=record_id,
                                              charge_mode=charge_mode):
                log.error("下机扣费失败: user_id = {} device_id = {} charge_mode = {}".format(
                    user_id, device_id, charge_mode))
                return fail(HTTP_OK, u"下机失败！")

            # 获得用户上线key
            user_key = get_user_key(user_id)
            # 获得设备上线key
            device_key = get_device_key(device_id)
            # 获得当前设备token
            device_code_key = get_device_code_key(device_code)
            # 获得keep_alive_key 更新最新存活时间
            keep_alive_key = get_keep_alive_key(record_key)

            # 从redis中删除上机记录
            redis.delete(record_key)
            redis.delete(user_key)
            redis.delete(device_key)
            redis.delete(device_code_key)
            redis.delete(keep_alive_key)

        except Exception as e:
            log.error("数据解析失败: {}".format(charging))
            log.exception(e)
            return fail(HTTP_OK, u"数据解析失败!!")
        finally:
            # 解锁
            if lock is not None:
                lock.release()
                log.info("下机完成: lock_key = {}".format(lock.lock_key))
        # finally:
        #     # 这里需要加锁
        #     if offline_lock_key is not None:
        #         redis.delete(offline_lock_key)
        #         log.info("下机解锁成功: {}".format(offline_lock_key))

        log.info("下机成功: user_id = {} device_id = {}".format(user_id, device_id))
        return success({'status': 1, 'msg': 'logout successed!'})

    @staticmethod
    def get_current_time_charging(charging_str):
        try:
            charge_dict = json.loads(charging_str)
            charge_dict['cur_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return charge_dict
        except Exception as e:
            log.error("json转换失败: charging = {}".format(charging_str))
            log.exception(e)
        return {'error': '计费json数据格式转换失败', 'status': -1}
