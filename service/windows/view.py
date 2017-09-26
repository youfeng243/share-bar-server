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

from flask import Blueprint
from flask import g
from flask import request

from exts.common import fail, HTTP_OK, log, success, LOGIN_ERROR_BIND, LOGIN_ERROR_DELETE, LOGIN_ERROR_FORBID, \
    LOGIN_ERROR_NOT_FIND, LOGIN_ERROR_NOT_SUFFICIENT_FUNDS, LOGIN_ERROR_UNKNOW, LOGIN_ERROR_DEVICE_IN_USING, \
    LOGIN_ERROR_USER_IN_USING, LOGIN_ERROR_DEVICE_NOT_FREE
from exts.database import redis
from exts.redis_dao import get_record_key, get_user_key, get_device_key, get_token_key
from service.device.model import Device
from service.use_record.model import UseRecord
from service.windows.impl import WindowsService
from tools.wechat_api import wechat_login_required, get_current_user

bp = Blueprint('windows', __name__, url_prefix='/windows')


# 扫描上线登录 需要确保微信端已经登录
@bp.route('/login/<device_code>', methods=['GET'])
@wechat_login_required
def login(device_code):
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
    # # 当前用户已经在线了
    # LOGIN_ERROR_USER_IN_USEING = -8
    # # 当前设备不处于空闲状态，不能上机
    # LOGIN_ERROR_DEVICE_NOT_FREE = -9

    # 获得用户信息
    user = get_current_user(g.openid)
    if user is None:
        log.warn("当前openid还未绑定手机号码: openid = {}".format(g.openid))
        return fail(HTTP_OK, u"用户还未登录!", LOGIN_ERROR_BIND)

    # 如果当前用户 被禁用 则不能上线
    if user.deleted is True:
        log.warn("当前用户已经被删除了，不能上线: user_id = {}".format(user.id))
        return fail(HTTP_OK, u"当前用户已经被删除了，不能上机", LOGIN_ERROR_DELETE)

    # 判断当前用户是否已经被禁用了
    if user.state == 'unused':
        log.warn("当前用户已经被禁用了，不能上线: user_id = {}".format(user.id))
        return fail(HTTP_OK, u"当前用户已经被禁用了，不能上线", LOGIN_ERROR_FORBID)

    # 获得设备信息
    device = Device.get_device_by_code(device_code=device_code)
    if device is None:
        log.warn("当前设备号没有对应的设备信息: device_code = {}".format(device_code))
        return fail(HTTP_OK, u"设备信息异常，设备不存在", LOGIN_ERROR_NOT_FIND)

    # 判断用户是否余额充足
    if user.balance_account <= 0:
        log.info("用户余额不足，不能上线: user_id = {} device_id = {} account = {}".format(
            user.id, device.id, user.balance_account))
        return fail(HTTP_OK, u"用户余额不足，不能上线!", LOGIN_ERROR_NOT_SUFFICIENT_FUNDS)

    # 判断是否已经在redis中进行记录
    record_key = get_record_key(user.id, device.id)
    # 获得用户上线key
    user_key = get_user_key(user.id)
    # 获得设备上线key
    device_key = get_device_key(device.id)
    # 获得当前设备token
    token_key = get_token_key(device_code)

    # 判断是否已经登录了
    charging = redis.get(record_key)
    if charging is None:

        # 判断当前设备是否已经在使用了
        if redis.get(device_key):
            log.warn("当前设备{}已经在被使用，但是用户ID = {}又在申请".format(device.id, user.id))
            return fail(HTTP_OK, u"当前设备已经在使用上线了，但是不是当前用户在使用!", LOGIN_ERROR_DEVICE_IN_USING)

        # 判断当前用户是否已经上线了
        if redis.get(user_key):
            log.warn("当前用户{}已经在上线，但是又在申请当前设备ID = {}".format(user.id, device.id))
            return fail(HTTP_OK, u"当前用户已经在使用上线了，但是不是当前设备在使用!", LOGIN_ERROR_USER_IN_USING)

        # 判断当前设备是否处于空闲状态
        if device.state != Device.STATE_FREE:
            log.warn("当前设备不处于空闲状态，不能上机: device_id = {} state = {}".format(device.id, device.state))
            return fail(HTTP_OK, u"当前设备不处于空闲状态，不能上机!", LOGIN_ERROR_DEVICE_NOT_FREE)

        log.info("用户还未上机进行上机: user_id = {} device_id = {}".format(user.id, device.id))
        record, is_success = UseRecord.create(user.id,
                                              device.id,
                                              device.address.province,
                                              device.address.city,
                                              device.address.area,
                                              device.address.location)
        if not is_success:
            log.warn("上线记录创建失败，上线失败: user_id = {} device_id = {}".format(user.id, device.id))
            return fail(HTTP_OK, u"上机记录创建失败!", LOGIN_ERROR_UNKNOW)

        log.info("当前上机时间: user_id:{} device_id:{} record_id:{} ctime:{}".format(
            user.id, device.id, record.id, record.ctime.strftime('%Y-%m-%d %H:%M:%S')))

        # 获得计费结构体
        charging = record.to_charging()
        # 得到计费方式
        charging['charge_mode'] = device.charge_mode
        # 得到当前用户总额
        charging['balance_account'] = user.balance_account
        # 填充设备机器码
        charging['device_code'] = device_code

        charge_str = json.dumps(charging)
        # 开始上线 把上线信息存储redis
        redis.set(record_key, charge_str)
        redis.set(user_key, charge_str)
        redis.set(device_key, charge_str)
        # 根据设备机器码获得记录token
        redis.set(token_key, record_key)

        # 设置设备当前使用状态
        device.state = Device.STATE_BUSY
        device.save()

    return success()


@bp.route('/offline', methods=['GET'])
@wechat_login_required
def wechat_offline():
    user = get_current_user(g.openid)
    if user is None:
        log.error("用户信息获取失败，无法下机: openid = {}".format(g.openid))
        return fail(HTTP_OK, u'用户信息获取失败，无法下机', -1)

    user_key = get_user_key(user.id)
    charging = redis.get(user_key)
    if charging is None:
        return success({
            'status': 0,
            'msg': "logout failed! reason: user device is already offline"})

    return WindowsService.do_logout(charging)


# 获取用户在线状态
@bp.route('/online/status', methods=['GET'])
@wechat_login_required
def get_online_status():
    user = get_current_user(g.openid)
    if user is None:
        log.error("用户信息获取失败，无法下机: openid = {}".format(g.openid))
        return fail(HTTP_OK, u'用户信息获取失败，无法获得上机状态信息', -1)
    user_key = get_user_key(user.id)
    charging = redis.get(user_key)
    if charging is None:
        return fail(HTTP_OK, u'当前用户没有上机信息', 0)

    return success(json.loads(charging))


# 判断设备是否已经上线登录
@bp.route('/check', methods=['POST'])
def check():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_code = request.json.get('device_code')
    if device_code is None:
        return fail(HTTP_OK, u"not have device_code!!!")

    token_key = get_token_key(device_code)
    record_key = redis.get(token_key)
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

    token = request.json.get('token')
    if token is None:
        return fail(HTTP_OK, u"not have token!!!")

    charging = redis.get(token)
    if charging is None:
        return success({
            "status": 0,
            "msg": "keepalive failed!reason:token invalid"})

    try:
        return success({
            "status": 1,
            "msg": "keepalive success",
            "data": json.loads(charging)})
    except Exception as e:
        log.error("json 加载失败: {}".format(charging))
        log.exception(e)

    return fail(HTTP_OK, u"json 数据解析失败!")


# 下线
@bp.route('/logout', methods=['POST'])
def logout():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    token = request.json.get('token')
    if token is None:
        return fail(HTTP_OK, u"not have token!!!")

    charging = redis.get(token)
    if charging is None:
        return success({
            'status': 0,
            'msg': "logout failed! reason: user device is already offline"})

    return WindowsService.do_logout(charging)
