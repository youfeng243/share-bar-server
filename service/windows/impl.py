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

from exts.common import log, fail, HTTP_OK, success, cal_cost_time
from exts.distributed_lock import DistributeLock
from exts.redis_api import RedisClient
from exts.resource import redis_client, db
from service.device.model import Device
from service.template.impl import TemplateService
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
            device.state = Device.STATUE_FREE

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

            # 计算下机时长
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
            user.total_cost_time += record.cost_time

            # 更新各属性时间
            user.utime = datetime.now()
            device.utime = datetime.now()
            record.utime = datetime.now()

            log.info("当前用户总的上机时长: user_id = {} total_cost_time = {}".format(
                user_id, user.total_cost_time))
            db.session.add(user)
            db.session.add(device)
            db.session.add(record)
            db.session.commit()

            return True, record, user
        except Exception as e:
            log.error("未知错误: user_id = {} device_id = {} record_id = {}".format(user_id, device_id, record_id))
            log.exception(e)
            db.session.rollback()

        return False, None, None

    # 上线操作
    @staticmethod
    def do_online(user, device, charge_mode):
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
        record_key = RedisClient.get_record_key(user.id, device.id)
        # 获得用户上线key
        user_key = RedisClient.get_user_key(user.id)
        # 获得设备上线key
        device_key = RedisClient.get_device_key(device.id)
        # 获得当前设备token
        device_code_key = RedisClient.get_device_code_key(device.device_code)

        # 获得keep_alive_key 更新最新存活时间
        keep_alive_key = RedisClient.get_keep_alive_key(record_key)

        log.info("当前上机时间: user_id:{} device_id:{} record_id:{} ctime:{}".format(
            user.id, device.id, record.id, record.ctime.strftime('%Y-%m-%d %H:%M:%S')))

        # 获得计费结构体
        charging = record.to_charging()
        # 得到计费方式
        charging['charge_mode'] = charge_mode
        # 得到当前用户总额
        charging['balance_account'] = user.balance_account
        # 填充设备机器码
        charging['device_code'] = device.device_code
        # 填充用户的openid
        charging['openid'] = user.openid

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
        lock = DistributeLock(user_key, redis_client)
        try:
            lock.acquire()

            # 开始上线 把上线信息存储redis
            redis_client.set(record_key, charge_str)
            redis_client.set(user_key, record_key)
            redis_client.set(device_key, record_key)
            # 根据设备机器码获得记录token
            redis_client.set(device_code_key, record_key)
            # 设置最新存活时间
            import time
            redis_client.set(keep_alive_key, int(time.time()))

            # 设置设备当前使用状态
            device.state = Device.STATUE_BUSY
            device.save()

            is_success = True
        except Exception as e:
            is_success = False
            log.exception(e)
        finally:
            lock.release()

        # 判断上线是否成功
        if is_success:
            # 发送上线通知
            TemplateService.online(user.openid,
                                   record.ctime,
                                   device.address,
                                   user.balance_account,
                                   charge_mode)

        return True

    @staticmethod
    def do_offline(charging):

        # offline_lock_key = None
        lock = None
        if charging is None:
            log.error("charging is None 下机异常!!")
            return fail(HTTP_OK, u"下机异常!")

        try:
            charge_dict = json.loads(charging)
            record_id = charge_dict.get('id')
            user_id = charge_dict.get('user_id')
            device_id = charge_dict.get('device_id')
            charge_mode = charge_dict.get('charge_mode')
            device_code = charge_dict.get('device_code')
            openid = charge_dict.get('openid')
            log.info("当前下线信息: user_id = {} device_id = {} charge_mode = {} device_code = {}".format(
                user_id, device_id, charge_mode, device_code))

            # 获得用户上线key
            user_key = RedisClient.get_user_key(user_id)

            #  下机需要加锁
            lock = DistributeLock(user_key, redis_client)

            log.info("开始加锁下机: user_key = {}".format(user_key))

            # 加锁下机
            lock.acquire()

            # 判断是否已经在redis中进行记录
            record_key = RedisClient.get_record_key(user_id, device_id)
            if redis_client.get(record_key) is None:
                log.warn("当前用户或者设备已经下机: user_id = {} device_id = {}".format(user_id, device_id))
                return success({'status': 1, 'msg': 'logout successed!'})

            # 结账下机
            result, record, user = WindowsService.cal_offline(user_id=user_id,
                                                              device_id=device_id,
                                                              record_id=record_id,
                                                              charge_mode=charge_mode)
            if not result:
                log.error("下机扣费失败: user_id = {} device_id = {} charge_mode = {}".format(
                    user_id, device_id, charge_mode))
                return fail(HTTP_OK, u"下机失败！")

            # 获得设备上线key
            device_key = RedisClient.get_device_key(device_id)
            # 获得当前设备token
            device_code_key = RedisClient.get_device_code_key(device_code)
            # 获得keep_alive_key 更新最新存活时间
            keep_alive_key = RedisClient.get_keep_alive_key(record_key)

            # 从redis中删除上机记录
            redis_client.delete(record_key)
            redis_client.delete(user_key)
            redis_client.delete(device_key)
            redis_client.delete(device_code_key)
            redis_client.delete(keep_alive_key)
            is_success = True
        except Exception as e:
            log.error("数据解析失败: {}".format(charging))
            log.exception(e)
            return fail(HTTP_OK, u"数据解析失败!!")
        finally:
            # 解锁
            if lock is not None:
                lock.release()
                log.info("下机完成: lock_key = {}".format(lock.lock_key))

        # 如果成功则进行下机提醒
        if is_success and openid is not None:
            TemplateService.offline(openid, record, user.balance_account)

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
