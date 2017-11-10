# -*- coding: utf-8 -*-

from __future__ import absolute_import

import redis

import settings
from exts.common import log, REDIS_PRE_RECORD_KEY, REDIS_PRE_USER_KEY, REDIS_PRE_DEVICE_KEY, \
    REDIS_PRE_DEVICE_CODE_KEY, REDIS_PRE_OPENID_KEY, REDIS_PRE_USER_ONLINE_KEY, REDIS_PRE_MOBILE_EX_KEY, \
    REDIS_PRE_CAPTCHA_EX_KEY, REDIS_PRE_DEVICE_HEART_KEY, REDIS_PRE_DEVICE_STATUS_KEY, REDIS_PRE_UPDATE_TIME_KEY, \
    REDIS_PRE_DEVICE_UPDATE_STATUS_KEY


class RedisClient(object):
    def __init__(self, db=0):
        self._client = redis.StrictRedis.from_url(settings.REDIS_URI,
                                                  db=db,
                                                  max_connections=settings.REDIS_MAX_CONNECTIONS)
        log.info("redis 初始化完成!!")

    def get(self, key):
        return self._client.get(key)

    def set(self, key, value):
        return self._client.set(key, value)

    # 设置过期时间
    def setex(self, key, ttl, value):
        return self._client.setex(key, ttl, value)

    def setnx(self, key, value):
        return self._client.setnx(key, value)

    def ttl(self, key):
        return self._client.ttl(key)

    def delete(self, key):
        return self._client.delete(key)

    def keys(self, pattern):
        return self._client.keys(pattern=pattern)

    def flushdb(self):
        return self._client.flushdb()

    # 获得用户上线使用记录key
    @staticmethod
    def get_record_key(user_id, device_id):
        record_key = "{record}{user_id}#{device_id}".format(record=REDIS_PRE_RECORD_KEY,
                                                            user_id=user_id,
                                                            device_id=device_id)
        return record_key

    # 获得用户上线key
    @staticmethod
    def get_user_key(user_id):
        user_key = "{}{}".format(REDIS_PRE_USER_KEY, user_id)
        return user_key

    # 获得设备上线key
    @staticmethod
    def get_device_key(device_id):
        device_key = "{}{}".format(REDIS_PRE_DEVICE_KEY, device_id)
        return device_key

    # 获得token key
    @staticmethod
    def get_device_code_key(device_code):
        return "{}{}".format(REDIS_PRE_DEVICE_CODE_KEY, device_code)

    # 获得openid access_token对应的存储key
    @staticmethod
    def get_openid_key(openid):
        return "{}{}".format(REDIS_PRE_OPENID_KEY, openid)

    @staticmethod
    def get_user_online_key(record_key):
        return "{}{}".format(REDIS_PRE_USER_ONLINE_KEY, record_key)

    # 获得存储在redis中的手机信息key
    @staticmethod
    def get_mobile_redis_key(mobile):
        return '{}{}'.format(REDIS_PRE_MOBILE_EX_KEY, mobile)

    # 获得存储在redis中的验证码信息key
    @staticmethod
    def get_captcha_redis_key(mobile):
        return '{}{}'.format(REDIS_PRE_CAPTCHA_EX_KEY, mobile)

    # 设备心跳的key
    @staticmethod
    def get_device_heart_key(device_code):
        return '{}{}'.format(REDIS_PRE_DEVICE_HEART_KEY, device_code)

    # 设备状态key
    @staticmethod
    def get_device_status_key(device_code):
        return '{}{}'.format(REDIS_PRE_DEVICE_STATUS_KEY, device_code)

    # 设备更新状态key
    @staticmethod
    def get_device_update_status_key(device_code):
        return '{}{}'.format(REDIS_PRE_DEVICE_UPDATE_STATUS_KEY, device_code)

    # 获得游戏更新时间
    @staticmethod
    def get_update_time_key():
        return REDIS_PRE_UPDATE_TIME_KEY
