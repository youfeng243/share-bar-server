#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: charge_manage.py
@time: 2017/10/2 21:24
"""

# 分布式锁
import time

from exts.common import log


class Lock(object):
    def __init__(self, key, redis_client, lock_timeout=3):
        self.redis_client = redis_client
        self.lock_timeout = lock_timeout
        self.lock_flag = 0
        self.lock_key = 'lock#' + key
        self.lock_time = self.lock_timeout + 1
        self.start_lock_time = 0

    # 加锁
    def acquire(self):
        log.info("开始加锁: {}".format(self.lock_key))
        self.start_lock_time = time.time()
        # 获取锁
        while self.lock_flag != 1:
            now = int(time.time())
            self.lock_time = now + self.lock_timeout + 1
            lock = self.redis_client.setnx(self.lock_key, self.lock_time)
            if lock == 1 or ((now > int(self.redis_client.get(self.lock_key))) and
                                     now > int(self.redis_client.getset(self.lock_key, self.lock_time))):
                break

            time.sleep(0.001)

    # 解锁
    def unlock(self):
        now = int(time.time())

        if now < self.lock_time:
            self.redis_client.delete(self.lock_key)
        log.info("解锁完成: {}".format(self.lock_key))
        log.info("加锁耗时: {}".format(time.time() - self.start_lock_time))
        log.info("加锁超时时长: {}".format(self.lock_timeout + 1))


# 后台计费管理
class ChargeManage(object):
    def __init__(self, redis_client):
        self.redis_client = redis_client
