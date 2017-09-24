# -*- coding: utf-8 -*-

from __future__ import absolute_import

import redis as r_

from exts.common import log


class Redis(object):
    def __init__(self, app=None):
        self._client = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        uri = app.config.get('REDIS_URI')
        max_conn = int(app.config.get('REDIS_MAX_CONNECTIONS', 32))
        self._client = r_.StrictRedis.from_url(uri, max_connections=max_conn)

        if not hasattr(app, 'extensions'):
            app.extensions = {}

        app.extensions['redis'] = self
        log.info("redis 初始化完成!!")

    def __getattr__(self, name):
        return getattr(self._client, name)

        # def set(self, key, value):
        #     self._client.set(key, value)


# 获得用户上线使用记录key
def get_record_key(user_id, device_id):
    record_key = "online#record#{user_id}#{device_id}".format(user_id=user_id, device_id=device_id)
    return record_key


# 获得用户上线key
def get_user_key(user_id):
    user_key = "online#player#{}".format(user_id)
    return user_key


# 获得设备上线key
def get_device_key(device_id):
    device_key = "online#device#{}".format(device_id)
    return device_key


# 获得token key
def get_token_key(device_code):
    return "online#token#{}".format(device_code)
