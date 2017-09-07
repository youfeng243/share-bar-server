#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/2 19:33
"""
from flask import Blueprint
from flask import request
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from exts.common import success, log, fail, HTTP_OK
from service.admin.model import Admin

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/sign_in', methods=['POST'])
def login():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username is None or password is None:
        log.warn("用户账号密码没有传过来...username = {} password = {}".format(
            username, password))
        return fail(HTTP_OK, u"没有用户密码信息!")

    # 获取是否需要记住密码
    is_remember = request.json.get('remember', False)

    admin = Admin.query.authenticate(username, password)
    if admin is not None:
        # 判断账户是否被停用
        if not admin.is_active():
            return fail(HTTP_OK, error=u'账户已被暂停使用,请联系管理员')

        if is_remember:
            login_user(admin, remember=True)
        else:
            login_user(admin, remember=False)
        log.info("用户登录成功: {} {}".format(username, password))
        return success(u'登录成功')

    admin = Admin.get_by_username(username)
    if admin is None:
        return fail(HTTP_OK, u'用户不存在')
    return fail(HTTP_OK, u'用户名或密码错误，请重新登陆!')


@bp.route('/sign_out', methods=['GET'])
@login_required
def logout():
    logout_user()
    return success(u"登出成功!")


# 测试用
@bp.route('/test', methods=['GET'])
@login_required
def test():
    log.info("当前属于登录状态...")
    return success(u"测试通过!")
