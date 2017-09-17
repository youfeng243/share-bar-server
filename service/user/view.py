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
from service.user.model import User

bp = Blueprint('user', __name__, url_prefix='/admin')


# 删除用户信息 批量功能
@bp.route('/user', methods=['DELETE'])
@login_required
def delete_user():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    result_list = []
    id_list = request.json.get('id_list', None)
    if not isinstance(id_list, list):
        log.warn("没有传入ID列表信息..")
        return fail(HTTP_OK, u"传入ID参数错误")

    for user_id in id_list:

        if not isinstance(user_id, int):
            log.warn("当前用户ID数据类型错误: {}".format(user_id))
            continue

        user = User.get(user_id)
        if user is None:
            log.warn("当前用户ID查找用户失败: {}".format(user_id))
            continue

        if not user.delete():
            log.warn("用户信息删除失败: {}".format(json.dumps(user.to_dict(), ensure_ascii=False)))
            continue
        result_list.append(user.id)

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
        if state not in User.STATE_VALUES:
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
    user = User.get_user_by_phone(user_id)
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
