#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/20 14:13
"""
import time

from flask import Blueprint
from flask import g
from flask import redirect
from flask import request
from flask import session
from flask import url_for
from flask_login import login_required

from exts.common import fail, HTTP_OK, log, success, LOGIN_ERROR_BIND, LOGIN_ERROR_DELETE, LOGIN_ERROR_FORBID, \
    LOGIN_ERROR_NOT_FIND, LOGIN_ERROR_NOT_SUFFICIENT_FUNDS, LOGIN_ERROR_UNKNOW, LOGIN_ERROR_DEVICE_IN_USING, \
    LOGIN_ERROR_USER_IN_USING, LOGIN_ERROR_DEVICE_NOT_FREE, decode_user_id, ATTENTION_URL
from exts.resource import redis_client
from exts.redis_api import get_record_key, get_user_key, get_device_key, get_device_code_key, get_keep_alive_key
from service.device.model import Device
from service.windows.impl import WindowsService
from tools.wechat_api import get_current_user, bind_required, get_wechat_user_info

bp = Blueprint('windows', __name__, url_prefix='/windows')


# 扫描上线登录 需要确保微信端已经登录
@bp.route('/login/<device_code>', methods=['GET'])
# @bind_required
def qr_code_online(device_code):
    # # 当前用户没有登录
    # LOGIN_ERROR_BIND = -1
    # # 当前用户已经被删除
    # LOGIN_ERROR_DELETE = -2
    # # 当前用户被禁止使用
    # LOGIN_ERROR_FORBID = -3
    # # 当前设备不存在
    # LOGIN_ERROR_NOT_FIND = -4
    # # 用户余额不足
    # LOGIN_ERROR_NOT_SUFFICIENT_FUNDS = -5
    # # 上线失败 未知错误
    # LOGIN_ERROR_UNKNOW = -6
    # # 设备已经在使用了
    # LOGIN_ERROR_DEVICE_IN_USEING = -7
    # # 当前用户已经在使用上线了，但是不是当前设备在使用
    # LOGIN_ERROR_USER_IN_USEING = -8
    # # 当前设备不处于空闲状态，不能上机
    # LOGIN_ERROR_DEVICE_NOT_FREE = -9

    scan_from = request.args.get('from')
    # 登录链接
    login_url = url_for("wechat.menu", name="login")
    # # 游戏链接
    # play_url = url_for("wechat.menu", name="playing")
    # # 账户链接
    # account_url = url_for("wechat.menu", name="account")

    # 通过微信二维码扫描则需要判断当前用户是否已经关注公众号
    if scan_from != 'playing':
        # # 初始化用户关注信息
        # subscribe, nick_name, head_img_url = 0, '', ''

        openid = session.get('openid', None)
        # 如果不是微信二维码扫描 则跳转到登录界面
        if openid is None:
            log.info("当前扫描登录没有openid，需要跳转到登录界面..")
            return redirect(login_url)

        # 获得用户的关注状态 以及头像和昵称信息
        subscribe, nick_name, head_img_url = get_wechat_user_info(openid)
        # 如果用户没有关注微信号 直接跳转到关注页面
        if subscribe != 1:
            log.info("当前用户没有关注公众号: subscribe = {} openid = {}".format(
                subscribe, openid))
            return redirect(ATTENTION_URL)

        # 如果当前用户已经关注 则直接跳转到 祥基指定的链接 2017-10-13 15:26:00
        url = '#/playing?code={}'.format(device_code)
        log.info("当前用户已经关注了公众号，跳转链接: {}".format(url))
        return redirect(url)

    user_id_cookie = session.get('u_id')
    if user_id_cookie is None:
        log.warn("当前session中没有u_id 信息，需要登录...")
        # if scan_from != 'playing':
        #     log.info("扫描不是来自上机界面按钮且没有登录, 需要跳转登录页面: url = {}".format(login_url))
        #     return redirect(login_url)
        return fail(HTTP_OK, u'当前用户没有登录', LOGIN_ERROR_BIND)

    user_id = decode_user_id(user_id_cookie)
    if user_id is None:
        log.warn("当前用户信息被篡改，需要重新登录: user_id_cookie = {}".format(user_id_cookie))
        # if scan_from != 'playing':
        #     log.info("扫描不是来自上机界面按钮且没有登录, 需要跳转登录页面: url = {}".format(login_url))
        #     return redirect(login_url)
        return fail(HTTP_OK, u'当前用户登录信息被篡改, 不能登录', LOGIN_ERROR_BIND)

    # 获得用户信息
    user = get_current_user(user_id)
    if user is None:
        log.warn("当前user_id还未绑定手机号码: user_id = {}".format(user_id))
        # if scan_from != 'playing':
        #     log.info("扫描不是来自上机界面按钮且没有登录, 需要跳转登录页面: url = {}".format(login_url))
        #     return redirect(login_url)

        return fail(HTTP_OK, u"用户还绑定手机号码登录!", LOGIN_ERROR_BIND)

    # # 判断当前用户是否已经关注了
    # if subscribe == 1:
    #     # 如果用户信息存储成功!!
    #     if UserService.save_nick_and_head(user, nick_name, head_img_url):
    #         log.info("通过微信二维码扫描上线的用户昵称信息与头像信息更新成功: user_id = {}".format(user.id))
    #     else:
    #         log.info("用户头像与昵称信息存储失败: user_id = {} nick_name = {} head_img_url = {}".format(
    #             user.id, nick_name, head_img_url))

    # 如果当前用户 被禁用 则不能上线
    if user.deleted is True:
        # if scan_from != 'playing':
        #     log.info("扫描不是来自上机界面按钮且当前用户已经被删除了, 需要跳转登录页面: url = {}".format(login_url))
        #     return redirect(login_url)

        log.warn("当前用户已经被删除了，不能上线: user_id = {}".format(user.id))
        return fail(HTTP_OK, u"当前用户已经被删除了，不能上机", LOGIN_ERROR_DELETE)

    # 判断当前用户是否已经被禁用了
    if user.state == 'unused':
        # if scan_from != 'playing':
        #     log.info("扫描不是来自上机界面按钮且当前用户已经被禁用了, 需要跳转登录页面: url = {}".format(login_url))
        #     return redirect(login_url)

        log.warn("当前用户已经被禁用了，不能上线: user_id = {}".format(user.id))
        return fail(HTTP_OK, u"当前用户已经被禁用了，不能上线", LOGIN_ERROR_FORBID)

    # 获得设备信息
    device = Device.get_device_by_code(device_code=device_code)
    if device is None:
        # if scan_from != 'playing':
        #     log.info("扫描不是来自上机界面按钮, 需要跳转: url = {}".format(play_url))
        #     return redirect(play_url)

        log.warn("当前设备号没有对应的设备信息: device_code = {}".format(device_code))
        return fail(HTTP_OK, u"设备信息异常，设备不存在", LOGIN_ERROR_NOT_FIND)

    # 判断用户是否余额充足 如果小于一分钟不能上机
    if user.balance_account < device.charge_mode:
        # if scan_from != 'playing':
        #     log.info("扫描不是来自上机界面按钮且当前用户余额不足, 需要跳转用户页面: url = {}".format(account_url))
        #     return redirect(account_url)

        log.info("用户余额不足，不能上线: user_id = {} device_id = {} account = {}".format(
            user.id, device.id, user.balance_account))
        return fail(HTTP_OK, u"用户余额不足，不能上线!", LOGIN_ERROR_NOT_SUFFICIENT_FUNDS)

    # 判断是否已经在redis中进行记录
    record_key = get_record_key(user.id, device.id)
    # 获得用户上线key
    user_key = get_user_key(user.id)
    # 获得设备上线key
    device_key = get_device_key(device.id)
    # # 获得当前设备token
    # device_code_key = get_device_code_key(device_code)

    # 判断是否已经登录了
    charging = redis_client.get(record_key)
    if charging is None:

        # 判断当前设备是否已经在使用了
        if redis_client.get(device_key):
            # if scan_from != 'playing':
            #     log.info("扫描不是来自上机界面按钮, 需要跳转: url = {}".format(play_url))
            #     return redirect(play_url)

            log.warn("当前设备{}已经在被使用，但是用户ID = {}又在申请".format(device.id, user.id))
            return fail(HTTP_OK, u"当前设备已经在使用上线了，但是不是当前用户在使用!", LOGIN_ERROR_DEVICE_IN_USING)

        # 判断当前用户是否已经上线了
        if redis_client.get(user_key):
            # if scan_from != 'playing':
            #     log.info("扫描不是来自上机界面按钮, 需要跳转: url = {}".format(play_url))
            #     return redirect(play_url)

            log.warn("当前用户{}已经在上线，但是又在申请当前设备ID = {}".format(user.id, device.id))
            return fail(HTTP_OK, u"当前用户已经在使用上线了，但是不是当前设备在使用!", LOGIN_ERROR_USER_IN_USING)

        # 判断当前设备是否处于空闲状态
        if device.state != Device.STATE_FREE:
            # if scan_from != 'playing':
            #     log.info("扫描不是来自上机界面按钮, 需要跳转: url = {}".format(play_url))
            #     return redirect(play_url)

            log.warn("当前设备不处于空闲状态，不能上机: device_id = {} state = {}".format(device.id, device.state))
            return fail(HTTP_OK, u"当前设备不处于空闲状态，不能上机!", LOGIN_ERROR_DEVICE_NOT_FREE)

        log.info("用户还未上机可以进行上机: user_id = {} device_id = {}".format(user.id, device.id))
        # record, is_success = UseRecord.create(user.id,
        #                                       device.id,
        #                                       device.address.province,
        #                                       device.address.city,
        #                                       device.address.area,
        #                                       device.address.location)
        if not WindowsService.do_online(user, device):
            # if scan_from != 'playing':
            #     log.info("扫描不是来自上机界面按钮, 需要跳转: url = {}".format(play_url))
            #     return redirect(play_url)

            log.warn("上线记录创建失败，上线失败: user_id = {} device_id = {}".format(user.id, device.id))
            return fail(HTTP_OK, u"上机异常!!", LOGIN_ERROR_UNKNOW)

    # 如果不是来自游戏仓按钮
    # if scan_from != 'playing':
    #     log.info("扫描不是来自上机界面按钮, 需要跳转: url = {}".format(play_url))
    #     return redirect(play_url)

    log.info("来自微信端游戏仓界面扫描: user_id = {} device_id = {}".format(user.id, device.id))
    return success()


@bp.route('/offline', methods=['GET'])
@bind_required
def wechat_offline():
    user_key = get_user_key(g.user_id)
    record_key = redis_client.get(user_key)
    if record_key is None:
        return success({
            'status': 0,
            'msg': "logout failed! reason: user device is already offline"})

    charging = redis_client.get(record_key)
    if charging is None:
        return success({
            'status': 0,
            'msg': "logout failed! reason: user device is already offline"})

    return WindowsService.do_offline(charging)


# 获取用户在线状态
@bp.route('/online/status', methods=['GET'])
@bind_required
def get_online_status():
    user_key = get_user_key(g.user_id)
    record_key = redis_client.get(user_key)
    if record_key is None:
        return fail(HTTP_OK, u'当前用户没有上机信息', 0)

    charging = redis_client.get(record_key)
    if charging is None:
        return fail(HTTP_OK, u'当前用户没有上机信息', 0)

    # charge_dict = json.loads(charging)
    # charge_dict['cur_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return success(WindowsService.get_current_time_charging(charging))


# 判断设备是否已经上线登录
@bp.route('/check', methods=['POST'])
def check_connect():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_code = request.json.get('device_code')
    if device_code is None:
        return fail(HTTP_OK, u"not have device_code!!!")

    device_code_key = get_device_code_key(device_code)
    record_key = redis_client.get(device_code_key)
    if record_key is None:
        return success({
            'status': 0,
            'msg': "not login"
        })

    return success({"status": 1, "token": record_key, "msg": "login successed!"})


# 心跳
@bp.route('/keepalive', methods=['POST'])
def keep_alive():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    record_key = request.json.get('token')
    if record_key is None:
        return fail(HTTP_OK, u"not have token!!!")

    charging = redis_client.get(record_key)
    if charging is None:
        return success({
            "status": 0,
            "msg": "keepalive failed!reason:token invalid"})

    # 获得keep_alive_key 更新最新存活时间
    keep_alive_key = get_keep_alive_key(record_key)

    # 设置最新存活时间
    redis_client.set(keep_alive_key, int(time.time()))

    # try:
    return success({
        "status": 1,
        "msg": "keepalive success",
        "data": WindowsService.get_current_time_charging(charging)})
    # except Exception as e:
    #     log.error("json 加载失败: {}".format(charging))
    #     log.exception(e)
    #
    # return fail(HTTP_OK, u"json 数据解析失败!")


# Windows端下线，使用的是 user_id#device_id
@bp.route('/logout', methods=['POST'])
def windows_offline():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    token = request.json.get('token')
    if token is None:
        return fail(HTTP_OK, u"not have token!!!")

    charging = redis_client.get(token)
    if charging is None:
        return success({
            'status': 0,
            'msg': "logout failed! reason: user device is already offline"})

    return WindowsService.do_offline(charging)


# 强制下机
@bp.route('/force/logout', methods=['POST'])
@login_required
def admin_offline():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    user_id = request.json.get('user_id')
    device_code = request.json.get('device_code')
    device_id = request.json.get('device_id')

    log.info("当前强制下机user_id = {}".format(user_id))
    log.info("当前强制下机device_code = {}".format(device_code))
    log.info("当前强制下机device_id = {}".format(device_id))

    if user_id is not None:
        user_key = get_user_key(user_id)
        record_key = redis_client.get(user_key)
        if record_key is None:
            return success({
                'status': 0,
                'msg': "logout failed! reason: user device is already offline"})

        charging = redis_client.get(record_key)
        if charging is None:
            return success({
                'status': 0,
                'msg': "logout failed! reason: user device is already offline"})
        log.info("通过user_id下机: user_id = {}".format(user_id))
        return WindowsService.do_offline(charging)

    if device_code is not None:
        device_code_key = get_device_code_key(device_code)
        record_key = redis_client.get(device_code_key)
        if record_key is not None:
            charging = redis_client.get(record_key)
            if charging is None:
                return success({
                    'status': 0,
                    'msg': "logout failed! reason: user device is already offline"})
            log.info("通过device_code下机: device_code = {}".format(device_code))
            return WindowsService.do_offline(charging)

    if device_id is not None:
        device_key = get_device_key(device_id)

        record_key = redis_client.get(device_key)
        if record_key is None:
            return success({
                'status': 0,
                'msg': "logout failed! reason: user device is already offline"})

        charging = redis_client.get(record_key)
        if charging is None:
            return success({
                'status': 0,
                'msg': "logout failed! reason: user device is already offline"})
        log.info("通过device_id下机: device_id = {}".format(device_id))
        return WindowsService.do_offline(charging)

    return success(u'当前参数没有使任何机器或用户下机')
