#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/20 14:13
"""
from flask import Blueprint
from flask import g
from flask import redirect
from flask import request
from flask import session

from exts.common import log, fail, HTTP_OK, success
from exts.sms import validate_captcha
from service.user.model import User
from tools.signature import check_signature, wechat_required

bp = Blueprint('wechat', __name__)


@bp.route('/', methods=['GET'])
@check_signature
def index():
    log.info("微信心跳....")
    return request.args.get('echostr')


# 进入自定义菜单
@bp.route('/wechat/menu/<name>', methods=['GET'])
@wechat_required
def menu(name):
    # 如果没授权 不允许访问
    if g.openid is None:
        return "Login Failed"

    # 如果没有注册，则先进入注册流程
    user = User.get_by_openid(g.openid)
    if user is None:
        return redirect('/login')

    # 进入账户中心
    if name == 'account':
        return redirect('/account')

    # 进入游戏仓
    if name == 'playing':
        return redirect('/playing')

    return fail(HTTP_OK, u"url error!")


# 用户登录
@bp.route('/wechat/login', methods=['POST'])
@wechat_required
def wechat_login():
    openid = session.get('openid', None)
    if openid is None:
        return fail(HTTP_OK, u'请使用微信客户端访问')

    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    mobile = request.json.get('mobile', None)
    if mobile is None:
        return fail(HTTP_OK, u'请输入手机号')

    code = request.json.get('code', None)
    if code is None:
        return fail(HTTP_OK, u'请输入验证码')

    # 校验手机验证码
    if validate_captcha(mobile, code):
        user = User.create(mobile, openid)
        return success(user.to_dict())

    return fail(HTTP_OK, u'验证码错误')
