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

from exts.common import fail, HTTP_OK, log, success
from exts.database import redis
from exts.redis_dao import get_record_key, get_user_key, get_device_key, get_token_key
from service.device.model import Device
from service.use_record.impl import UseRecordService
from service.use_record.model import UseRecord
from service.user.impl import UserService
from tools.wechat_api import wechat_required

bp = Blueprint('windows', __name__, url_prefix='/windows')


# 扫描上线登录 需要确保微信端已经登录
@bp.route('/login/<device_code>', methods=['GET'])
@wechat_required
def login(device_code):
    if g.openid is None:
        return fail(HTTP_OK, u"请使用微信端进行操作!")

    # 获得用户信息
    user = UserService.get_by_openid(g.openid)
    if user is None:
        log.warn("当前openid还未绑定手机号码: openid = {}".format(g.openid))
        return fail(HTTP_OK, u"用户还未登录!")

    # 如果当前用户 被禁用 则不能上线
    if user.deleted is True:
        log.warn("当前用户已经被删除了，不能上线: user_id = {}".format(user.id))
        return fail(HTTP_OK, u"当前用户已经被删除了，不能上机")

    # 判断当前用户是否已经被禁用了
    if user.state == 'unused':
        log.warn("当前用户已经被禁用了，不能上线: user_id = {}".format(user.id))
        return fail(HTTP_OK, u"当前用户已经被禁用了，不能上线")

    # 获得设备信息
    device = Device.get_device_by_code(device_code=device_code)
    if device is None:
        log.warn("当前设备号没有对应的设备信息: device_code = {}".format(device_code))
        return fail(HTTP_OK, u"设备信息异常，设备不存在")

    # 判断用户是否余额充足
    if user.balance_account <= 0:
        log.info("用户余额不足，不能上线: user_id = {} device_id = {} account = {}".format(
            user.id, device.id, user.balance_account))
        return fail(HTTP_OK, u"用户余额不足，不能上线!")

    # 判断是否已经在redis中进行记录
    record_key = get_record_key(user.id, device.id)
    # 获得用户上线key
    user_key = get_user_key(user.id)
    # 获得设备上线key
    device_key = get_device_key(device.id)
    # 获得当前设备token
    token_key = get_token_key(device_code)

    # 判断是否已经登录了
    record_id = redis.get(record_key)
    if record_id is None:
        log.info("用户还未登录进行登录: user_id = {} device_id = {}".format(user.id, device.id))
        record, is_success = UseRecord.create(user.id,
                                              device.id,
                                              device.address.province,
                                              device.address.city,
                                              device.address.area,
                                              device.address.location)
        if not is_success:
            log.warn("上线记录创建失败，上线失败: user_id = {} device_id = {}".format(user.id, device.id))
            return fail(HTTP_OK, u"上机记录创建失败!")

        # 获得计费结构体
        charging = record.to_charging()
        # 得到计费方式
        charging['charge_mode'] = device.charge_mode
        # 得到当前用户总额
        charging['balance_account'] = user.balance_account
        # 填充设备机器码
        charging['device_code'] = device_code

        # 开始上线 把上线信息存储redis
        redis.set(record_key, json.dumps(charging))
        redis.set(user_key, record.id)
        redis.set(device_key, record.id)
        # 根据设备机器码获得记录token
        redis.set(token_key, record_key)

        # 设置设备当前使用状态
        device.state = Device.STATE_BUSY
        device.save()

    return success()


# 判断设备是否已经上线登录
@bp.route('/check/<device_code>', methods=['GET'])
def check(device_code):
    token_key = get_token_key(device_code)
    record_key = redis.get(token_key)
    if record_key is None:
        return success({
            'status': 0,
            'msg': "not login"
        })

    return success({"status": 1, "token": record_key, "msg": "login successed!"})


# 心跳
@bp.route('/keepalive/<token>', methods=['GET'])
def keep_alive(token):
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
@bp.route('/logout/<token>', methods=['GET'])
def logout(token):
    charging = redis.get(token)
    if charging is None:
        return success({
            'status': 0,
            'msg': "logout failed! reason: user device is already offline"})

    try:
        charge_dict = json.loads(charging)
        record_id = charge_dict.get('id')
        user_id = charge_dict.get('user_id')
        device_id = charge_dict.get('device_id')
        charge_mode = charge_dict.get('charge_mode')
        device_code = charge_dict.get('device_code')
        log.info("当前下线信息: user_id = {} device_id = {} charge_mode = {} device_code = {}".format(
            user_id, device_id, charge_mode, device_code))

        # 结账下机
        if not UseRecordService.cal_offline(user_id=user_id,
                                            device_id=device_id,
                                            record_id=record_id,
                                            charge_mode=charge_mode):
            return fail(HTTP_OK, u"下机失败！")

            # 判断是否已经在redis中进行记录
        record_key = get_record_key(user_id, device_id)
        # 获得用户上线key
        user_key = get_user_key(user_id)
        # 获得设备上线key
        device_key = get_device_key(device_id)
        # 获得当前设备token
        token_key = get_token_key(device_code)

        # 从redis中删除上机记录
        redis.delete(record_key)
        redis.delete(user_key)
        redis.delete(device_key)
        redis.delete(token_key)

    except Exception as e:
        log.error("数据解析失败: {}".format(charging))
        log.exception(e)
        return fail(HTTP_OK, u"数据解析失败!!")

    return success({'status': 1,
                    'msg': 'logout successed!'})
