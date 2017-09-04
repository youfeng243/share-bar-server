# !/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: gun.config.py
@time: 2017/8/28 20:45
"""

from flask import Flask

import settings
from common import log, fail, HTTP_BAD_REQUEST, HTTP_FORBIDDEN, HTTP_NOT_FOUND, HTTP_SERVER_ERROR
from exts.database import db


def create_app(name=None):
    app = Flask(name or __name__)

    # 从settings中加载配置信息
    app.config.from_object('settings')

    app.debug = settings.DEBUG

    # 数据库初始化
    db.init_app(app)

    # 设置错误处理流程
    setup_error_handler(app)

    return app


def setup_error_handler(app):
    @app.errorhandler(400)
    @app.errorhandler(ValueError)
    def http_bad_request(e):
        log.exception(e)
        return fail(HTTP_BAD_REQUEST)

    @app.errorhandler(403)
    def http_forbidden(e):
        log.exception(e)
        return fail(HTTP_FORBIDDEN)

    @app.errorhandler(404)
    def http_not_found(e):
        log.exception(e)
        return fail(HTTP_NOT_FOUND)

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def http_server_error(e):
        log.exception(e)
        return fail(HTTP_SERVER_ERROR)
