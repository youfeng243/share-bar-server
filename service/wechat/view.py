#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/20 14:13
"""
import json
from datetime import datetime

from flask import Blueprint
from flask import g
from flask import redirect
from flask import request
from flask import url_for

import settings
from exts.common import log, fail, HTTP_OK, success
from exts.database import redis
from exts.sms import validate_captcha
from service.recharge.impl import RechargeService
from service.recharge.model import Recharge
from service.use_record.model import UseRecord
from service.user.impl import UserService
from tools.wechat_api import wechat_login_required, get_user_wechat_info, get_current_user, get_nonce_str, \
    gen_jsapi_signature, \
    wechat_token_required
from tools.wx_pay import WxPay, WxPayError
from tools.xml_data import XMLData

bp = Blueprint('wechat', __name__, url_prefix='/wechat')


# 进入自定义菜单
@bp.route('/menu/<name>', methods=['GET'])
@wechat_login_required
def menu(name):
    # 如果没有注册，则先进入注册流程
    user = get_current_user(g.openid)
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


# 判断当前用户是否已经登录
@bp.route('/check', methods=['GET'])
@wechat_token_required
def wechat_check():
    user = get_current_user(g.openid)
    if user is None:
        log.info("当前openid没有注册用户信息: {}".format(g.openid))
        return fail(HTTP_OK, u"当前openid没有注册!", 0)

    return success()


# 用户登录
@bp.route('/login', methods=['POST'])
@wechat_login_required
def wechat_login():
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
        user = UserService.get_user_by_mobile(mobile)
        if user is None:
            # 获得用户的头像与昵称信息
            head_img_url, nike_name = get_user_wechat_info(g.refresh_token, g.openid)
            log.info("当前用户获取的信息为: openid = {} head = {} nikename = {}".format(
                g.openid, head_img_url, nike_name))
            user, is_success = UserService.create(mobile, g.openid,
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
@wechat_login_required
def get_user_info():
    user = get_current_user(g.openid)
    if user is None:
        log.warn("当前openid没有获得用户信息: {}".format(g.openid))
        return fail(HTTP_OK, u'没有当前用户信息')

    # 判断昵称或头像是否已经获取到了
    if user.head_img_url == '' or user.nike_name == '':
        # 先判断token是否存在
        head_img_url, nike_name = get_user_wechat_info(g.refresh_token, g.openid)
        if head_img_url == '' or nike_name == '':
            log.error("再次更新用户ID = {} 头像与昵称失败: head_img_url = {} nike_name = {}".format(
                user.id, head_img_url, nike_name))
        else:
            # 存储用户信息
            user.head_img_url = head_img_url
            user.nike_name = nike_name
            if user.save():
                log.info("重新更新用户昵称与头像成功: user_id = {} head = {} nike = {}".format(
                    user.id, user.head_img_url, user.nike_name))

    return success(user.to_dict())


# 支付回调
@bp.route("/notify", methods=['POST', 'GET'])
def notify():
    log.info("当前回调携带数据为: data = {}".format(request.data))
    data_dict = XMLData.parse(request.data)
    log.info("进入支付响应回调...")
    if data_dict.return_code != 'SUCCESS' or data_dict.result_code != 'SUCCESS':
        log.warn("支付失败: {}".format(request.data))
        return fail(HTTP_OK, '支付失败!')

    log.info("开始进行支付记录存储!!")

    # 微信订单
    transaction_id = data_dict.transaction_id

    # 用户ID信息
    user_id = int(data_dict.attach)

    wx_pay = WxPay(
        wx_app_id=settings.WECHAT_APP_ID,  # 微信平台appid
        wx_mch_id=settings.WECHAT_MCH_ID,  # 微信支付商户号
        wx_mch_key=settings.WECHAT_PAYMENT_SECRET,
        # wx_mch_key 微信支付重要密钥，请登录微信支付商户平台，在 账户中心-API安全-设置API密钥设置
        wx_notify_url=""
        # wx_notify_url 接受微信付款消息通知地址（通常比自己把支付成功信号写在js里要安全得多，推荐使用这个来接收微信支付成功通知）
        # wx_notify_url 开发详见https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_7
    )
    try:
        log.info("当前查询订单: user_id = {} transaction_id = {}".format(user_id, transaction_id))
        result = wx_pay.order_query(transaction_id=transaction_id)
        if result is None:
            log.warn("查询订单失败: {}".format(transaction_id))
            return fail(HTTP_OK, '查询订单失败!')

        if result.get('return_code') != 'SUCCESS' or \
                        result.get('result_code') != 'SUCCESS':
            log.warn("查询订单返回结果失败: {}".format(transaction_id))
            return fail(HTTP_OK, '查询订单失败!')

        if 'total_fee' not in result:
            log.warn('订单返回信息, total_fee not in result: {}'.format(json.dumps(result, ensure_ascii=False)))
            return fail(HTTP_OK, '解析订单信息失败!')

        # 订单金额
        total_fee = result.get('total_fee', 0)
        if total_fee < 0:
            total_fee = 0

        if 'time_end' not in result:
            log.warn('订单返回信息, time_end not in result: {}'.format(json.dumps(result, ensure_ascii=False)))
            return fail(HTTP_OK, '解析订单信息失败!')

        # 支付时间
        pay_time = datetime.strptime(result.get('time_end', "20170926111841"), '%Y%m%d%H%M%S')

        # 如果充值记录已经存在则不再存储
        if RechargeService.find_by_transaction_id(transaction_id) is not None:
            log.info("当前记录已经存储过，不在进行存储: {}".format(transaction_id))
            return success()

        # 创建充值记录
        obj, is_success = RechargeService.create(user_id, total_fee, transaction_id, pay_time)
        if not is_success:
            return fail(HTTP_OK, u"充值记录存储失败!")

        return success()
    except Exception as e:
        log.error("查询订单失败:")
        log.exception(e)

    return fail(HTTP_OK, u"回调查询订单失败!!!")


# 充值接口
@bp.route("/recharge/<int:account>", methods=['GET'])
@wechat_login_required
def recharge(account):
    user = get_current_user(g.openid)
    if user is None:
        log.warn("当前openid没有获得用户信息: {}".format(g.openid))
        return fail(HTTP_OK, u'没有当前用户信息')

    if account <= 0:
        log.warn("充值金额不正确: account = {}".format(account))
        return fail(HTTP_OK, u"充值金额数目不正确，需要正整数!")

    notify_url = url_for('wechat.notify', _external=True)
    log.info("支付回调url = {}".format(notify_url))
    wx_pay = WxPay(
        wx_app_id=settings.WECHAT_APP_ID,  # 微信平台appid
        wx_mch_id=settings.WECHAT_MCH_ID,  # 微信支付商户号
        wx_mch_key=settings.WECHAT_PAYMENT_SECRET,
        # wx_mch_key 微信支付重要密钥，请登录微信支付商户平台，在 账户中心-API安全-设置API密钥设置
        wx_notify_url=notify_url
        # wx_notify_url 接受微信付款消息通知地址（通常比自己把支付成功信号写在js里要安全得多，推荐使用这个来接收微信支付成功通知）
        # wx_notify_url 开发详见https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_7
    )
    try:
        log.info("当前支付用户ID = {}".format(user.id))
        pay_data = wx_pay.js_pay_api(
            openid=user.openid,  # 付款用户openid
            body=u'Account Recharge',  # 例如：饭卡充值100元
            total_fee=account,  # total_fee 单位是 分， 100 = 1元
            attach=str(user.id),
        )
    except WxPayError as e:
        log.error("支付失败: openid = {} mobile = {}".format(user.openid, user.mobile))
        log.exception(e)
        return fail(HTTP_OK, e.message)

    log.info("当前支付结果: {}".format(json.dumps(pay_data, ensure_ascii=False)))
    return success(pay_data)


# 获得充值列表
@bp.route("/recharge/list", methods=['POST'])
@wechat_login_required
def get_recharge_list():
    '''
    page: 当前页码
    size: 每页读取数目, 最大不超过50项
    start_time: 查询的起始时间段 时间段其实时间必须小于或者等于end_time
    end_time: 查询的结束时间段 时间段必须大于或者等于start_time
    :return:
    '''
    # {
    #     "page": 1,
    #
    #     "size": 10,
    #     "user_id": 100
    # }

    user = get_current_user(g.openid)
    if user is None:
        log.warn("当前openid没有获得用户信息: {}".format(g.openid))
        return fail(HTTP_OK, u'没有当前用户信息')

    return Recharge.search_list(_user_id=user.id)


# 消费记录列表
@bp.route("/expense/list", methods=['POST'])
@wechat_login_required
def get_expense_list():
    user = get_current_user(g.openid)
    if user is None:
        log.warn("当前openid没有获得用户信息: {}".format(g.openid))
        return fail(HTTP_OK, u'没有当前用户信息')

    return UseRecord.search_list(_user_id=user.id)


# 获得wx.config
@bp.route("/jsapi/signature", methods=['POST'])
@wechat_login_required
def get_jsapi_signature():
    user = get_current_user(g.openid)
    if user is None:
        log.warn("当前openid没有获得用户信息: {}".format(g.openid))
        return fail(HTTP_OK, u'没有当前用户信息')

    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    url = request.json.get('url')
    if url is None:
        log.warn("没有传入url 参数: {}".format(json.dumps(request.json, ensure_ascii=False)))
        return fail(HTTP_OK, u"没有传入url参数!")

    jsapi_ticket = redis.get(settings.WECHAT_JSAPI_TICKET_KEY)
    if jsapi_ticket is None:
        log.warn("没有jsapi_ticket: openid = {}".format(g.openid))
        return fail(HTTP_OK, u'没有jsapi_ticket')

    import time
    timestamp = int(time.time())
    nonceStr = get_nonce_str(31)
    signature = gen_jsapi_signature(timestamp, nonceStr, jsapi_ticket, url)
    config = {
        'debug': True,
        'appId': settings.WECHAT_APP_ID,
        'timestamp': timestamp,
        'nonceStr': nonceStr,
        'signature': signature,
        'jsApiList': ['scanQRCode']
    }

    log.info("当前openid获取的wx.config = {}".format(json.dumps(config, ensure_ascii=False)))
    return success(config)
