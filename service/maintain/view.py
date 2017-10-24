#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/10/24 14:40
"""
from flask import Blueprint
from flask import request
from flask_login import login_required

from exts.common import log, HTTP_OK, fail, success
from service.maintain.impl import MaintainService

bp = Blueprint('maintain', __name__, url_prefix='/admin')


# 获得维护人员列表信息
@bp.route('/maintain/list', methods=['POST'])
@login_required
def get_maintain_list():
    return MaintainService.search_list()


# 创建维护人员信息
@bp.route('/maintain', methods=['POST'])
@login_required
def create_maintain():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    username = request.json.get('username')
    name = request.json.get('name')
    password = request.json.get('password')
    address_id = request.json.get('address_id')

    if not isinstance(username, basestring) or \
            not isinstance(name, basestring) or \
            not isinstance(password, basestring) or \
            not isinstance(address_id, int):
        return fail(HTTP_OK, u"参数错误")

    username = username.strip()
    name = name.strip()
    password = password.strip()
    if username == '' or name == '' or password == '':
        log.error("当前有参数为空字符串: username = {} name = {} password = {}".format(
            username, name, password))
        return fail(HTTP_OK, u"参数不能为空字符串!!")

    maintain, is_success = MaintainService.create(username, password, name, address_id)
    if not is_success or maintain is None:
        log.error("创建维护人员失败: username = {} password = {} name = {} address_id = {}".format(
            username, password, name, address_id))
        return fail(HTTP_OK, u"创建维护人员失败!!!")

    log.info("创建维护人员成功: username = {} password = {} name = {} address_id = {}".format(
        username, password, name, address_id))
    return success(u'创建维护人员成功!', id=maintain.id)


# 修改维护人员接口
@bp.route('/maintain', methods=['PUT'])
@login_required
def update_maintain():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    maintain_id = request.json.get('id')
    name = request.json.get('name')
    password = request.json.get('password')
    address_id = request.json.get('address_id')

    is_success = MaintainService.update_maintain(maintain_id, name, password, address_id)
    if not is_success:
        return fail(HTTP_OK, u"更新失败!")

    return success(u'更新维护人员信息成功!', id=maintain_id)


# 删除维护人员接口
@bp.route('/maintain', methods=['DELETE'])
@login_required
def delete_maintain():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    id_list = request.json.get('list', None)
    if not isinstance(id_list, list):
        log.warn("参数错误: id_list = {}".format(id_list))
        return fail(HTTP_OK, u"传入不是id列表")

    result_list = []
    for maintain_id in id_list:
        if not MaintainService.delete_maintain(maintain_id):
            log.warn("当前维护人员删除失败: maintain_id = {}".format(maintain_id))
            continue

        result_list.append(maintain_id)
    return success(result_list)
