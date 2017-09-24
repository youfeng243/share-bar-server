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
from flask import request

import settings
from exts.common import log, fail, HTTP_BAD_REQUEST, HTTP_FORBIDDEN, HTTP_NOT_FOUND, HTTP_SERVER_ERROR
from exts.database import db, redis
from exts.login_manager import setup_admin_login
from service.address.view import bp as address_bp
from service.admin.view import bp as admin_bp
from service.captcha.view import bp as captcha_bp
from service.deploy.view import bp as deploy_bp
from service.device.view import bp as device_bp
from service.recharge.view import bp as recharge_bp
from service.role.view import bp as role_bp
from service.user.view import bp as user_bp
from service.wechat.view import bp as wechat_bp
from service.windows.view import bp as windows_bp


def create_app(name=None):
    app = Flask(name or __name__)

    # 从settings中加载配置信息
    app.config.from_object('settings')

    app.debug = settings.DEBUG

    # 数据库初始化
    db.init_app(app)

    # redis 初始化
    redis.init_app(app)

    # 管理员登录管理
    setup_admin_login(app)

    # 设置错误处理流程
    setup_error_handler(app)

    # 注册蓝图
    register_bp(app)

    # 注册访问日志钩子
    setup_hooks(app)

    log.info("flask 服务初始化完成...")
    return app


# 注册蓝图
def register_bp(app):
    app.register_blueprint(admin_bp)
    app.register_blueprint(address_bp)
    app.register_blueprint(deploy_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(wechat_bp)
    app.register_blueprint(captcha_bp)
    app.register_blueprint(recharge_bp)
    app.register_blueprint(windows_bp)


def _request_log(resp, *args, **kwargs):
    log.info(
        '{addr} request: [{status}] {method}, '
        'url: {url}'.format(addr=request.remote_addr,
                            status=resp.status,
                            method=request.method,
                            url=request.url,
                            )
    )
    if resp.mimetype == 'application/json':
        log.info(resp.get_data())
    return resp


def setup_hooks(app):
    app.after_request(_request_log)


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
