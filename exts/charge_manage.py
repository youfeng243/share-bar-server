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


# def sync(key, lock_time=4):
#     def decorator(func):
#         def _decorator(*args, **kwargs):
#             # 加锁的redis 键
#             lock_key = 'sync#' + key
#
#             ret = func(*args, **kwargs)
#
#             return ret
#
#         return _decorator
#
#     return decorator


# LOCK_TIMEOUT = 3
# lock = 0
# lock_timeout = 0
# lock_key = 'lock.foo'
#
# # 获取锁
# while lock != 1:
#     now = int(time.time())
#     lock_timeout = now + LOCK_TIMEOUT + 1
#     lock = redis_client.setnx(lock_key, lock_timeout)
#     if lock == 1 or (now > int(redis_client.get(lock_key))) and now > int(redis_client.getset(lock_key, lock_timeout)):
#         break
#     else:
#         time.sleep(0.001)
#
# # 已获得锁
# do_job()
#
# # 释放锁
# now = int(time.time())
# if now < lock_timeout:
#     redis_client.delete(lock_key)

class Lock(object):
    def __init__(self, key, redis_client, lock_timeout=3):
        self.redis_client = redis_client
        self.lock_timeout = lock_timeout
        self.lock_flag = 0
        self.lock_key = 'lock#' + key
        self.lock_time = self.lock_timeout + 1

    # 加锁
    def acquire(self):

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


# 后台计费管理
class ChargeManage(object):
    def __init__(self, redis_client):
        self.redis_client = redis_client
