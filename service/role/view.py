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
from service.role.model import Role

bp = Blueprint('role', __name__, url_prefix='/admin')

'''
1. 角色分页列表查询 [finish]
2. 角色删除 [finish]
3. 角色编辑，修改角色名称 [finish]
4. 添加角色 [finish]
5. 根据角色ID 或者 角色名称查询角色 [finish]
'''


# 根据角色ID 或者角色名称查询角色
@bp.route('/role/<role_info>', methods=['GET'])
@login_required
def get_role(role_info):
    if not isinstance(role_info, basestring) or role_info.strip() == '':
        log.warn("传入参数有误: location = {}".format(role_info))
        return fail(HTTP_OK, u"参数错误!")

    role = Role.get_by_name(role_info)
    if role is not None:
        return success(role.to_dict())

    try:
        a_id = int(role_info)
        role = Role.get(a_id)
        if role is not None:
            return success([role.to_dict()])
    except Exception as e:
        log.error("角色名称信息无法转换为 int 类型: role_info = {}".format(role_info))
        log.exception(e)

    return success(None)


# 获得角色列表
@bp.route('/role/list', methods=['POST'])
@login_required
def get_role_list():
    '''
    page: 当前页码
    size: 每页读取数目, 最大不超过50项
    '''
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    page = request.json.get('page')
    size = request.json.get('size')

    if not isinstance(page, int) or \
            not isinstance(size, int):
        log.warn("请求参数错误: page = {} size = {}".format(page, size))
        return fail(HTTP_OK, u"请求参数错误")

        # 请求参数必须为正数
    if page <= 0 or size <= 0:
        msg = "请求参数错误: page = {} size = {}".format(
            page, size)
        log.error(msg)
        return fail(HTTP_OK, msg)

    if size > 50:
        log.info("翻页最大数目只支持50个, 当前size超过50 size = {}!".format(size))
        size = 50

    return success(Role.find_role_list(page, size))


# 删除角色
@bp.route('/role/<int:role_id>', methods=['DELETE'])
@login_required
def delete_role(role_id):
    role = Role.get(role_id)
    if role is None:
        log.warn("通过当前ID没有查到角色信息: role_id = {}".format(role_id))
        return fail(HTTP_OK, u"角色信息不存在!")

    if not role.delete():
        log.warn("设备信息删除失败: {}".format(json.dumps(role.to_dict(), ensure_ascii=False)))
        return fail(HTTP_OK, u"角色设备信息失败!")
    return success(role.id)


# 添加角色
@bp.route('/role', methods=['POST'])
@login_required
def add_role():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    name = request.json.get('name')
    if not isinstance(name, basestring):
        return fail(HTTP_OK, u"角色名称数据类型不正确!")

    if Role.get_by_name(name) is not None:
        return fail(HTTP_OK, u"当前角色名称已经存在!")

    role, is_success = Role.create(name)
    if not is_success:
        return fail(HTTP_OK, u"角色创建失败!")

    return success(role.to_dict())


# 编辑角色
@bp.route('/role', methods=['PUT'])
@login_required
def edit_role():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    role_id = request.json.get('id')
    if not isinstance(role_id, int):
        return fail(HTTP_OK, u"角色ID数据类型不正确!")

    role = Role.get(role_id)
    if role is None:
        log.warn("当前角色ID没有查找到对应的角色信息: id = {}".format(role_id))
        return fail(HTTP_OK, u"当前角色ID不存在!")

    name = request.json.get('name')
    if not isinstance(name, basestring):
        return fail(HTTP_OK, u"角色名称数据类型不正确!")

    # 如果当前角色名称没变 则直接返回成功
    if role.name == name:
        return success(role.to_dict())

    if Role.get_by_name(name) is not None:
        log.warn("当前角色名称已经存在: {}".format(name))
        return fail(HTTP_OK, u"当前角色名称已经存在，不能重复")

    role.name = name
    if not role.save():
        return fail(HTTP_OK, u"当前角色信息存储错误!")

    return success(role.to_dict())
