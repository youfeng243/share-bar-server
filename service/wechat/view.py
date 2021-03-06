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
from flask import session

import settings
from exts.common import log, fail, HTTP_OK, success, WECHAT_JSAPI_TICKET_KEY, encode_user_id, decode_user_id
from exts.geetest import GeetestLib
from exts.resource import redis_cache_client, sms_client
from service.recharge.impl import RechargeService
from service.recharge.model import Recharge
from service.use_record.model import UseRecord
from service.user.impl import UserService
from tools.wechat_api import wechat_required, get_current_user, gen_jsapi_signature, \
    bind_required, \
    get_current_user_by_openid, get_wechat_user_info
from tools.wx_pay import WxPay, WxPayError
from tools.xml_data import XMLData

bp = Blueprint('wechat', __name__, url_prefix='/wechat')

# 微信支付初始化
notify_url = 'http://weixin.doumihuyu.com/wechat/notify'
log.info("支付回调url = {}".format(notify_url))
wx_pay = WxPay(
    wx_app_id=settings.WECHAT_APP_ID,  # 微信平台appid
    wx_mch_id=settings.WECHAT_MCH_ID,  # 微信支付商户号
    wx_mch_key=settings.WECHAT_PAYMENT_SECRET,
    # wx_mch_key 微信支付重要密钥，请登录微信支付商户平台，在 账户中心-API安全-设置API密钥设置
    wx_notify_url=notify_url
)


# 进入自定义菜单
@bp.route('/menu/<name>', methods=['GET'])
# 需要绑定手机号 才能够进入菜单系统
@wechat_required
# 一定需要登录了才能够进入账户系统
# @bind_required
def menu(name):
    # url跳转
    def redirect_to(action_name):
        # 进入账户中心
        if action_name == 'account':
            log.info("跳转到/account页面...")
            return redirect('#/account')

        # 进入游戏仓
        if action_name == 'playing':
            log.info("跳转到/playing页面...")
            return redirect('#/playing')

        log.info("无法处理请求: action_name = {} 跳转到登录界面".format(action_name))
        return redirect('#/login')

    # 判断是否已经绑定了微信
    def already_bind_openid(openid):
        user_info = UserService.get_by_openid(openid)
        if user_info is not None and user_info.deleted == False:
            log.info("当前需要登录的: openid = {}".format(openid))

            # 生成对应的cookie
            u_id = encode_user_id(user_info.id)
            session['u_id'] = u_id
            log.info("当前绑定的user_id cookie = {}".format(u_id))

            return redirect_to(name)
        return redirect('#/login')

    # 判断当前用户是否已经绑定
    user_id_cookie = session.get('u_id')
    if user_id_cookie is None:
        log.warn("当前session中没有u_id 信息，需要登录...")
        return already_bind_openid(g.openid)

    user_id = decode_user_id(user_id_cookie)
    if user_id is None:
        log.warn("当前用户信息被篡改，需要重新登录: user_id_cookie = {}".format(user_id_cookie))
        return already_bind_openid(g.openid)

    # 如果user_id 不存在 则需要重新登录绑定
    user = get_current_user(user_id)
    if user is None:
        log.warn("数据库中没有当前用户信息，需要登录: user_id = {}".format(user_id))
        return already_bind_openid(g.openid)

    if user.deleted:
        log.warn("当前用户被删除，需要重新登录: user_id = {}".format(user_id))
        return redirect('#/login')

    return redirect_to(name)


# 判断当前用户是否微信端授权
@bp.route('/check', methods=['GET'])
def wechat_check():
    openid = session.get('openid', None)
    # refresh_token = session.get('refresh_token', None)
    # 如果两个关键的token都存在 则正常进入下面的流程
    if openid is None:
        log.warn("当前用户没有openid..")
        return fail(HTTP_OK, u"当前用户没有openid!", -1)

    user = get_current_user_by_openid(openid)
    if user is None:
        log.info("当前openid没有注册用户信息: {}".format(openid))
        return fail(HTTP_OK, u"当前openid没有注册!", 0)

    if user.deleted:
        log.info("当前openid没有注册用户信息: {}".format(openid))
        return fail(HTTP_OK, u"当前用户已经被删除!", -2)

    return success()


# 获取极验初始化信息
@bp.route('/geetest', methods=['GET'])
@wechat_required
def geetest():
    # 初始化极验验证码
    gt = GeetestLib(settings.PC_GEETEST_ID, settings.PC_GEETEST_KEY)
    status = gt.pre_process(g.openid)
    session[gt.GT_STATUS_SESSION_KEY] = status
    response_str = gt.get_response_str()
    log.info("极验验证码初始化状态: response_str = {}".format(response_str))

    return success(json.loads(response_str))


# 请求手机验证码，进行用户注册
@bp.route('/captcha', methods=['POST'])
@wechat_required
def request_code():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    mobile = request.json.get('mobile', None)
    if mobile is None:
        return fail(HTTP_OK, u'手机号不能为空')

    if not isinstance(mobile, basestring):
        log.warn("当前手机号: mobile = {}".format(mobile))
        log.warn("当前手机号的类型: mobile type = {}".format(type(mobile)))
        return fail(HTTP_OK, u'手机号不合法')

    mobile = mobile.strip()
    if len(mobile) != 11:
        log.warn("当前手机号: mobile = {}".format(mobile))
        return fail(HTTP_OK, u'手机号不合法')

    if sms_client.mobile_reach_rate_limit(mobile):
        return fail(HTTP_OK, u'验证码已发送')

    gt = GeetestLib(settings.PC_GEETEST_ID, settings.PC_GEETEST_KEY)
    challenge = request.json.get(gt.FN_CHALLENGE)
    validate = request.json.get(gt.FN_VALIDATE)
    seccode = request.json.get(gt.FN_SECCODE)
    status = session.get(gt.GT_STATUS_SESSION_KEY)

    if status:
        result = gt.success_validate(challenge, validate, seccode, g.openid)
    else:
        result = gt.failback_validate(challenge, validate, seccode)

    log.info("滑动验证码参数: mobile = {} {} {}".format(mobile, gt.FN_CHALLENGE, challenge))
    log.info("滑动验证码参数: mobile = {} {} {}".format(mobile, gt.FN_VALIDATE, validate))
    log.info("滑动验证码参数: mobile = {} {} {}".format(mobile, gt.FN_SECCODE, seccode))
    log.info("当前滑动验证码破解情况: result = {}".format(result))
    if result <= 0:
        log.info("当期手机号滑动验证码破解失败，不进行短信验证码请求: {}".format(mobile))
        return fail(HTTP_OK, u'滑动验证码识别失败，无法请求短信验证码!')

    # 通过手机号请求验证码
    if sms_client.request_sms(mobile):
        return success()

    return fail(HTTP_OK, u"发送验证码请求失败!")


# 用户登录
@bp.route('/login', methods=['POST'])
@wechat_required
def wechat_login():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    mobile = request.json.get('mobile', None)
    if mobile is None:
        return fail(HTTP_OK, u'请输入手机号')

    if not isinstance(mobile, basestring):
        return fail(HTTP_OK, u"手机号不合法")

    if len(mobile.strip()) != 11:
        return fail(HTTP_OK, u'手机号不合法')

    code = request.json.get('code', None)
    if code is None:
        return fail(HTTP_OK, u'请输入验证码')

    if not isinstance(code, basestring):
        return fail(HTTP_OK, u"验证码不合法")

    if code.strip() == '':
        return fail(HTTP_OK, u'请输入验证码')

    mobile = mobile.strip()
    code = code.strip()

    # 如果验证码错误
    if not sms_client.validate_captcha(mobile, code):
        return fail(HTTP_OK, u'验证码错误')

    user = UserService.get_user_by_mobile(mobile)

    # 校验完成正确
    if user is not None and user.openid == g.openid:
        u_id = encode_user_id(user.id)
        session['u_id'] = u_id
        log.info("当前绑定的user_id cookie = {}".format(u_id))
        # 去除用户删除标志
        user.deleted = False
        user.save()
        return success(user.to_dict())

    if user is not None and user.openid != g.openid:
        log.info("当前手机号码已绑定其他微信，不能登录: openid = {} mobile = {}".format(
            g.openid, mobile))
        return fail(HTTP_OK, u"当前手机号码已绑定其他微信，不能登录!")

    # 如果能够通过openid找到对应的用户信息则说明当前openid已经绑定过了，不能登录
    user = UserService.get_by_openid(g.openid)
    if user is not None:
        log.info("当前微信已绑定其他手机号，不能登录: openid = {} mobile = {}".format(
            g.openid, mobile))
        return fail(HTTP_OK, u"当前微信已绑定其他手机号，不能登录!")

    # 如果手机号与微信号都没有任何记录，则需要建立账号

    # 获得用户的头像与昵称信息
    subscribe, nick_name, head_img_url = get_wechat_user_info(g.openid)
    log.info("当前用户获取的信息为: openid = {} head = {} nick_name = {}".format(
        g.openid, head_img_url, nick_name))
    user, is_success = UserService.create(mobile, g.openid,
                                          head_img_url=head_img_url,
                                          nick_name=nick_name)
    if not is_success:
        log.error("创建用户信息异常: openid = {}".format(g.openid))
        return fail(HTTP_OK, u"创建新用户失败!")

    u_id = encode_user_id(user.id)
    session['u_id'] = u_id
    log.info("当前绑定的user_id cookie = {}".format(u_id))
    return success(user.to_dict())


# 获取当前用户信息接口
@bp.route('/user', methods=['GET'])
@wechat_required
@bind_required
def get_user_info():
    user = get_current_user(g.user_id)
    if user is None:
        log.warn("当前user_id没有获得用户信息: {}".format(g.user_id))
        return fail(HTTP_OK, u'没有当前用户信息')

    if user.deleted:
        log.warn("当前user_id用户已经被删除: {}".format(g.user_id))
        return fail(HTTP_OK, u'当前用户已经被删除')

    # 判断昵称或头像是否已经获取到了
    if user.head_img_url == '' or user.nick_name == '':
        # 先判断token是否存在
        subscribe, nick_name, head_img_url = get_wechat_user_info(user.openid)
        if head_img_url == '' or nick_name == '':
            log.error("再次更新用户ID = {} 头像与昵称失败: head_img_url = {} nick_name = {}".format(
                user.id, head_img_url, nick_name))
        else:
            # 存储用户昵称和头像信息
            if UserService.save_nick_and_head(user, nick_name, head_img_url):
                log.info("重新更新用户昵称与头像成功: user_id = {} head = {} nike = {}".format(
                    user.id, user.head_img_url, user.nick_name))

                # # 存储用户信息
                # user.head_img_url = head_img_url
                # user.nick_name = nick_name
                # if user.save():
                #     log.info("重新更新用户昵称与头像成功: user_id = {} head = {} nike = {}".format(
                #         user.id, user.head_img_url, user.nick_name))

    return success(user.to_dict())


# 支付回调
@bp.route("/notify", methods=['POST', 'GET'])
def notify():
    # log.info("当前回调携带数据为: data = {}".format(request.data))
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

    try:
        # 如果充值记录已经存在则不再存储
        if RechargeService.find_by_transaction_id(transaction_id) is not None:
            log.info("当前记录已经存储过，不在进行存储: {}".format(transaction_id))
            return success()

        log.info("当前通过微信查询订单: user_id = {} transaction_id = {}".format(user_id, transaction_id))
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
        # 如果不为数值 则改为数值
        if isinstance(total_fee, basestring):
            total_fee = int(total_fee)
        if total_fee < 0:
            total_fee = 0

        if 'time_end' not in result:
            log.warn('订单返回信息, time_end not in result: {}'.format(json.dumps(result, ensure_ascii=False)))
            return fail(HTTP_OK, '解析订单信息失败!')

        # 支付时间
        pay_time = datetime.strptime(result.get('time_end', "20170926111841"), '%Y%m%d%H%M%S')

        log.info("当前充值记录还未存在，存储记录: transaction_id = {}".format(transaction_id))
        # 创建充值记录
        obj, is_success = RechargeService.create(user_id, total_fee, transaction_id, pay_time)
        if not is_success:
            log.error("存储充值记录失败: user_id = {} transaction_id = {}".format(
                user_id, transaction_id))
            return fail(HTTP_OK, u"充值记录存储失败!")

        # 如果当前用户正在上线则需要更新redis中的总余额数据
        RechargeService.online_recharge(user_id, total_fee)

        return success()
    except Exception as e:
        log.error("查询订单失败:")
        log.exception(e)

    return fail(HTTP_OK, u"回调查询订单失败!!!")


# 充值接口
@bp.route("/recharge/<int:account>", methods=['GET'])
@wechat_required
@bind_required
def recharge(account):
    if account <= 0:
        log.warn("充值金额不正确: account = {}".format(account))
        return fail(HTTP_OK, u"充值金额数目不正确，需要正整数!")

    try:
        log.info("当前支付用户ID = {}".format(g.user_id))
        pay_data = wx_pay.js_pay_api(
            openid=g.openid,  # 付款用户openid
            body=u'Account Recharge',  # 例如：饭卡充值100元
            total_fee=account,  # total_fee 单位是 分， 100 = 1元
            attach=str(g.user_id),
        )
    except WxPayError as e:
        log.error("支付失败: openid = {} user_id = {}".format(g.openid, g.user_id))
        log.exception(e)
        return fail(HTTP_OK, e.message)

    log.info("当前支付结果: {}".format(json.dumps(pay_data, ensure_ascii=False)))
    return success(pay_data)


# 获得充值列表
@bp.route("/recharge/list", methods=['POST'])
@bind_required
def get_recharge_list():
    '''
    page: 当前页码
    size: 每页读取数目, 最大不超过50项
    start_time: 查询的起始时间段 时间段其实时间必须小于或者等于end_time
    end_time: 查询的结束时间段 时间段必须大于或者等于start_time
    :return:
    '''

    return Recharge.search_list(_user_id=g.user_id)


# 消费记录列表
@bp.route("/expense/list", methods=['POST'])
@bind_required
def get_expense_list():
    return UseRecord.search_list(_user_id=g.user_id)


# 获得wx.config
@bp.route("/jsapi/signature", methods=['POST'])
@bind_required
def get_jsapi_signature():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    url = request.json.get('url')
    if url is None:
        log.warn("没有传入url 参数: {}".format(json.dumps(request.json, ensure_ascii=False)))
        return fail(HTTP_OK, u"没有传入url参数!")

    jsapi_ticket = redis_cache_client.get(WECHAT_JSAPI_TICKET_KEY)
    if jsapi_ticket is None:
        log.warn("没有jsapi_ticket: user_id = {}".format(g.user_id))
        return fail(HTTP_OK, u'没有jsapi_ticket')

    import time
    timestamp = int(time.time())
    nonceStr = wx_pay.nonce_str(31)
    signature = gen_jsapi_signature(timestamp, nonceStr, jsapi_ticket, url)
    config = {
        'debug': settings.DEBUG,
        'appId': settings.WECHAT_APP_ID,
        'timestamp': str(timestamp),
        'nonceStr': nonceStr,
        'signature': signature,
        'jsApiList': ['scanQRCode']
    }

    log.info("当前user_id获取的wx.config = {}".format(json.dumps(config, ensure_ascii=False)))
    return success(config)
