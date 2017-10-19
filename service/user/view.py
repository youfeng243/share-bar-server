#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/14 20:16
"""
import json

from flask import Blueprint
from flask import request
from flask_login import login_required

from exts.common import log, fail, HTTP_OK, success
from exts.redis_api import RedisClient
from exts.resource import redis_client
from service.use_record.model import UseRecord
from service.user.impl import UserService
from service.user.model import User
from service.windows.impl import WindowsService

bp = Blueprint('user', __name__, url_prefix='/admin')


# 删除用户信息 批量功能
@bp.route('/user', methods=['DELETE'])
@login_required
def delete_user():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    result_list = []
    user_list = request.json.get('list', None)
    if not isinstance(user_list, list):
        log.warn("没有传入ID列表信息..")
        return fail(HTTP_OK, u"传入ID参数错误")

    for user_id in user_list:

        if not isinstance(user_id, int):
            log.warn("当前用户ID数据类型错误: {}".format(user_id))
            continue

        user = User.get(user_id)
        if user is None:
            log.warn("当前用户ID查找用户失败: {}".format(user_id))
            continue

        if user.deleted:
            log.warn("当前用户信息已经被删除: {}".format(user_id))
            continue

        if not user.delete():
            log.warn("用户信息删除失败: {}".format(json.dumps(user.to_dict(), ensure_ascii=False)))
            continue
        result_list.append(user.id)
    log.info("删除用户信息成功: {}".format(result_list))
    return success(result_list)


# 改变用户状态 批量功能
@bp.route('/user', methods=['PUT'])
@login_required
def change_user_state():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    result_list = []
    user_list = request.json.get('list', None)
    if not isinstance(user_list, list):
        log.warn("没有传入ID列表信息..")
        return fail(HTTP_OK, u"传入ID参数错误")

    for item in user_list:

        user_id = item.get('id', None)
        if not isinstance(user_id, int):
            log.warn("当前用户ID数据类型错误: {}".format(user_id))
            continue

        state = item.get('state', None)
        if state not in User.STATUS_VALUES:
            log.warn("传入的状态信息不正确: user_id = {} state = {}".format(user_id, state))
            continue

        user = User.get(user_id)
        if user is None:
            log.warn("当前用户ID查找用户失败: {}".format(user_id))
            continue

        if not user.change_state(state):
            log.warn('当前用户状态信息修改失败: {}'.format(json.dumps(user.to_dict(), ensure_ascii=False)))
            continue

        result_list.append(user.to_dict())

    return success(result_list)


# 根据用户ID 用户手机号码查找
@bp.route('/user/<user_id>', methods=['GET'])
@login_required
def get_user_by_id(user_id):
    # 先通过手机号码查找
    user = UserService.get_user_by_mobile(user_id)
    if user is not None:
        return success(user.to_dict())

    try:
        a_id = int(user_id)
        user = User.get(a_id)
        if user is not None:
            return success(user.to_dict())
    except Exception as e:
        log.error("用户ID信息无法转换为 int 类型: user_id = {}".format(user_id))
        log.exception(e)

    return success(None)


# 根据查询条件返回用户信息
@bp.route('/user/list', methods=['POST'])
@login_required
def get_user_list():
    return User.search_list()


# 获得用户使用记录
@bp.route('/user/records', methods=['POST'])
@login_required
def get_user_use_records():
    # {
    #     "page": 1,
    #
    #     "size": 10,
    #     "user_id": 100
    #     "order_by" "+cost_time" or "-cost_time" or "+cost_money" or "-cost_money"
    # }
    return UseRecord.search_list()


# 强制下机
@bp.route('/user/force/logout', methods=['POST'])
@login_required
def user_offline():
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
        user_key = RedisClient.get_user_key(user_id)
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
        device_code_key = RedisClient.get_device_code_key(device_code)
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
        device_key = RedisClient.get_device_key(device_id)

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
