#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/9/26 16:54
"""
import json

from exts.charge_manage import Lock
from exts.common import log
from exts.database import redis
from exts.redis_dao import get_user_key, get_record_key, get_device_key


class WechatService(object):
    # 给指定在线用户充值
    @staticmethod
    def online_recharge(user_id, total_fee):
        # # 判断是否已经在redis中进行记录
        # record_key = get_record_key(user.id, device.id)
        # # 获得用户上线key
        # user_key = get_user_key(user.id)
        # # 获得设备上线key
        # device_key = get_device_key(device.id)

        # 开始上线 把上线信息存储redis
        # redis.set(record_key, charge_str)
        # redis.set(user_key, charge_str)
        # redis.set(device_key, charge_str)

        # return {
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
        #     'cost_time': self.cost_time
        #     'balance_account':
        # }
        # 先获得用户缓存的信息
        user_key = get_user_key(user_id)

        # todo 这里需要加锁, 否则扣费下机时会有影响
        lock = Lock(user_key, redis)

        try:
            lock.acquire()
            charge_str = redis.get(user_key)
            if charge_str is None:
                log.info("当前用户没有在线，不需要同步在线数据: user_id = {}".format(user_id))
                return

            try:
                charge_dict = json.loads(charge_str)
                if charge_dict is None:
                    log.error("解析json数据失败: {}".format(charge_str))
                    return

                device_id = charge_dict.get('device_id')
                balance_account = charge_dict.get('balance_account')

                if not isinstance(device_id, int):
                    log.error("device_id 数据类型不正确: {}".format(device_id))
                    return

                if not isinstance(balance_account, int):
                    log.error("balance_account 数据类型不正确: {}".format(balance_account))
                    return

                charge_dict['balance_account'] = balance_account + total_fee
                redis.set(user_key, json.dumps(charge_dict))

                # 修改组合的数据信息
                record_key = get_record_key(user_id, device_id)
                charge_str = redis.get(record_key)
                if charge_str is None:
                    log.info("当前用户没有在线，不需要同步在线数据: user_id = {}".format(user_id))
                    return

                charge_dict = json.loads(charge_str)
                if charge_dict is None:
                    log.error("解析json数据失败: {}".format(charge_str))
                    return

                charge_dict['balance_account'] = balance_account + total_fee
                redis.set(record_key, json.dumps(charge_dict))

                device_key = get_device_key(device_id)
                charge_str = redis.get(device_key)
                if charge_str is None:
                    log.info("当前用户没有在线，不需要同步在线数据: user_id = {}".format(user_id))
                    return

                charge_dict = json.loads(charge_str)
                if charge_dict is None:
                    log.error("解析json数据失败: {}".format(charge_str))
                    return

                charge_dict['balance_account'] = balance_account + total_fee
                redis.set(device_key, json.dumps(charge_dict))
                log.info("同步修改redis中用户上机信息成功! user_id = {} account = {}".format(user_id, balance_account + total_fee))
            except Exception as e:
                log.error("解析json数据失败: {}".format(charge_str))
                log.exception(e)
        finally:
            lock.unlock()
