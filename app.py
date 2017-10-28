# !/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: gun.config.py
@time: 2017/8/28 20:45
"""
import json

from flask import Flask
from flask import request

import settings
from exts.common import log, fail, HTTP_BAD_REQUEST, HTTP_FORBIDDEN, HTTP_NOT_FOUND, HTTP_SERVER_ERROR, \
    DEFAULT_GAME_UPDATE_TIME
from exts.login_manager import setup_admin_login
from exts.resource import db
from service.address.view import bp as address_bp
from service.admin.view import bp as admin_bp
from service.charge.view import bp as charge_bp
from service.deploy.view import bp as deploy_bp
from service.device.impl import GameService
from service.device.view import bp as device_bp
from service.maintain.view import bp as maintain_bp
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

    # 管理员登录管理
    setup_admin_login(app)

    # 设置错误处理流程
    setup_error_handler(app)

    # 注册蓝图
    register_bp(app)

    # 注册访问日志钩子
    setup_hooks(app)

    # 设置更新时间
    set_game_update_time()

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
    app.register_blueprint(recharge_bp)
    app.register_blueprint(windows_bp)
    app.register_blueprint(charge_bp)
    app.register_blueprint(maintain_bp)


# 设置游戏更新时间
def set_game_update_time():
    if GameService.get_game_update_time() is None:
        GameService.set_game_update_time(DEFAULT_GAME_UPDATE_TIME)


def _get_remote_addr():
    address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if address is not None:
        # An 'X-Forwarded-For' header includes a comma separated list of the
        # addresses, the first address being the actual remote address.
        address = address.encode('utf-8').split(b',')[0].strip()
    return address


def _request_log(resp, *args, **kwargs):
    log.info(
        '{addr} request: [{status}] {method}, '
        'url: {url}'.format(addr=_get_remote_addr(),
                            status=resp.status,
                            method=request.method,
                            url=request.url,
                            )
    )
    # 不是debug模式下也需要打印数据信息
    if resp.mimetype == 'application/json':
        data = resp.get_data()
        log.info("response: {}".format(json.dumps(json.loads(data), ensure_ascii=False)))
    return resp


def setup_hooks(app):
    # 调试模式下显示请求日志
    if app.debug:
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
