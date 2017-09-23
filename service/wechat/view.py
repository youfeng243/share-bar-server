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
from tools.wechat_api import wechat_required, get_user_wechat_info, get_current_user

bp = Blueprint('wechat', __name__, url_prefix='/wechat')


# 进入自定义菜单
@bp.route('/menu/<name>', methods=['GET'])
@wechat_required
def menu(name):
    # 如果没授权 不允许访问
    if g.openid is None:
        log.info("还未获得openid: name = {}".format(name))
        return "Login Failed"

    # 如果没有注册，则先进入注册流程
    user = User.get_by_openid(g.openid)
    if user is None:
        log.info("账户还没注册, 需要进入登录流程..")
        return redirect('/login')

    # 判断是否需要重新登录
    if name == 'login':
        log.info("当前用户需要重新登录: openid = {}".format(g.openid))
        return redirect('/login')

    # 进入账户中心
    if name == 'account':
        log.info("跳转到/account页面...")
        return redirect('/account')

    # 进入游戏仓
    if name == 'playing':
        log.info("跳转到/playing页面...")
        return redirect('/playing')

    log.info("无法处理请求: name = {}".format(name))
    return fail(HTTP_OK, u"url error!")


# 用户登录
@bp.route('/login', methods=['POST'])
@wechat_required
def wechat_login():
    if g.openid is None:
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
        user = User.get_user_by_phone(mobile)
        if user is None:
            # 获得用户的头像与昵称信息
            head_img_url, nike_name = get_user_wechat_info(session['access_token'], g.openid)
            log.info("当前用户获取的信息为: openid = {} head = {} nikename = {}".format(
                g.openid, head_img_url, nike_name))
            user = User.create(mobile, g.openid,
                               head_img_url=head_img_url,
                               nike_name=nike_name)
        elif user.openid != g.openid:
            user.openid = g.openid
            if not user.save():
                log.warn("user mobile = {} openid = {} 存储错误!".format(mobile, g.openid))
                return fail(HTTP_OK, u"user 存储错误!")

        return success(user.to_dict())

    return fail(HTTP_OK, u'验证码错误')


# 获取当前用户信息接口
@bp.route('/user', methods=['GET'])
@wechat_required
def get_user_info():
    user = get_current_user()
    if user is None:
        log.warn("当前openid没有获得用户信息: {}".format(g.openid))
        return fail(HTTP_OK, u'没有当前用户信息')

    return success(user.to_dict())
