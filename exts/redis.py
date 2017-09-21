# -*- coding: utf-8 -*-

from __future__ import absolute_import

import redis as r_


# redis 存储一些到点需要过期的信息 比如微信登录 获得短信验证码过期
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

    def __getattr__(self, name):
        return getattr(self._client, name)
