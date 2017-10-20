#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: distributed_lock.py
@time: 2017/10/2 21:24
"""

# 分布式锁
import time

from exts.common import log


class DistributeLock(object):
    def __init__(self, key, redis_cache_client, lock_timeout=3):
        self.__redis = redis_cache_client
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
            lock = self.__redis.setnx(self.lock_key, self.lock_time)
            if lock == 1 or ((now > int(self.__redis.get(self.lock_key))) and
                                     now > int(self.__redis.getset(self.lock_key, self.lock_time))):
                break

            time.sleep(0.001)
        log.info("获取锁成功: {}".format(self.lock_key))

    # 解锁
    def release(self):
        now = int(time.time())

        if now < self.lock_time:
            self.__redis.delete(self.lock_key)
            log.info("删除加锁key成功: lock_key = {}".format(self.lock_key))
        log.info("解锁完成: {}".format(self.lock_key))
        log.info("加锁耗时: {}s".format(time.time() - self.start_lock_time))
        log.info("设置加锁超时时长: {}s".format(self.lock_timeout + 1))
