#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/10/17 23:22
"""
import json

from flask import Blueprint
from flask import request
from flask_login import login_required

from exts.common import log, HTTP_OK, fail, success
from service.charge.impl import ChargeService
from service.charge.model import Charge

bp = Blueprint('charge', __name__, url_prefix='/admin')


# 创建费率
@bp.route('/charge', methods=['POST'])
@login_required
def new_charge():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    # json = {
    #     'name': 'xxx',
    #     'charge_mode': 'xxxx',
    # }

    name = request.json.get('name', None)
    charge_mode = request.json.get('charge_mode', None)
    if name is None or not isinstance(charge_mode, int) or charge_mode <= 0:
        log.warn("参数错误: name = {} charge_mode = {}".format(name, charge_mode))
        return fail(HTTP_OK, u"name or charge_mode 参数错误!")

    if ChargeService.find_by_name(name) is not None:
        log.warn("费率命名冲突, 数据库中已存在名字相同的费率模板: name = {}".format(name))
        return fail(HTTP_OK, u"费率命名冲突, 数据库中已存在名字相同的费率模板: name = {}".format(name))

    charge, is_success = ChargeService.create(name, charge_mode)
    if not is_success:
        log.warn("创建费率模板失败: name = {} charge_mode = {}".format(name, charge_mode))
        return fail(HTTP_OK, u"创建费率模板失败: name = {} charge_mode = {}".format(name, charge_mode))

    return success(charge.to_dict())


# 获得费率列表
@bp.route('/charge/list', methods=['POST'])
@login_required
def get_charge_list():
    return Charge.search_list()


# 删除费率
# 批量删除设备
@bp.route('/charge', methods=['DELETE'])
@login_required
def delete_charges():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    id_list = request.json.get('list', None)
    if not isinstance(id_list, list):
        log.warn("参数错误: id_list = {}".format(id_list))
        return fail(HTTP_OK, u"传入不是id列表")

    result_list = []
    for charge_id in id_list:
        charge = Charge.get(charge_id)
        if charge is None:
            log.warn("当前ID设备信息不存在: {}".format(charge_id))
            continue

        if not charge.delete():
            log.warn("费率信息删除失败: {}".format(json.dumps(charge.to_dict(), ensure_ascii=False)))
            continue

        result_list.append(charge_id)

    # 如果当前费率有被成功删除的，则需要更新redis中的费率信息
    # if len(result_list) > 0:
    #     charge = ChargeService.update_charge_to_redis()
    #     if charge is not None:
    #         log.info("完成一次 redis 中费率更新: 最新费率 charge_mode = {}".format(charge.charge_mode))
    #     else:
    #         log.info("更新费率到redis失败!")

    return success(result_list)


# 修改费率
@bp.route('/charge', methods=['PUT'])
@login_required
def update_charges():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    charge_id = request.json.get('id', None)
    if charge_id is None:
        log.warn("参数错误: charge_id 为None")
        return fail(HTTP_OK, u"参数错误: charge_id 为None")

    charge = Charge.get(charge_id)
    if charge is None:
        log.warn("当前费率模板不存在: charge_id = {}".format(charge_id))
        return fail(HTTP_OK, u"当前费率模板不存在: charge id = {}".format(charge))

    name = request.json.get('name', None)
    charge_mode = request.json.get('charge_mode', None)
    if not isinstance(name, basestring) and not isinstance(charge_mode, int):
        return fail(HTTP_OK, u"需要修改的参数错误，至少需要传入一个需要修改的参数")

    if isinstance(name, basestring) and name.strip() != '':
        other_charge = ChargeService.find_by_name(name.strip())
        if other_charge is not None and other_charge.id != charge.id:
            log.error("修改名称重复: charge_id = {} charge_name = {}".format(charge_id, name))
            return fail(HTTP_OK, u"需要修改的模板名称重复!")
        charge.name = name.strip()
    else:
        return fail(HTTP_OK, u'费率模板名称不能为空字符串!')

    if isinstance(charge_mode, int) and charge_mode > 0:
        charge.charge_mode = charge_mode
    else:
        return fail(HTTP_OK, u"charge_mode 参数类型错误!")

    if not charge.save():
        return fail(HTTP_OK, u"费率模板存储错误!")

    return success(charge.to_dict())

# 获得当前最新费率
# @bp.route('/charge/newest', methods=['GET'])
# @login_required
# def newest_charge():
#     charge = ChargeService.update_charge_to_redis()
#     if charge is not None:
#         log.info("完成一次 redis 中费率更新: 最新费率 charge_mode = {} ctime = {} ".format(
#             charge.charge_mode, charge.ctime.strftime('%Y-%m-%d %H:%M:%S')))
#         return success(charge.to_dict())
#
#     log.info("更新费率到redis失败!")
#     return fail(HTTP_OK, u"费率更新失败!")
