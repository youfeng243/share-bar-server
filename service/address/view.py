#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/7 20:32
"""
import json

from flask import Blueprint
from flask import request
from flask_login import login_required

from exts.common import fail, HTTP_OK, log, success
from service.address.model import Address

bp = Blueprint('address', __name__, url_prefix='/admin')


# 删除地址 [finish]
@bp.route('/address', methods=['DELETE'])
@login_required
def delete_address():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    id_list = request.json.get('list', None)
    if not isinstance(id_list, list):
        log.warn("参数错误: id_list = {}".format(id_list))
        return fail(HTTP_OK, u"传入不是id列表")

    result_list = []
    for address_id in id_list:
        # 查找地址是否已经存在
        address = Address.get(address_id)
        if address is None:
            log.warn("地址信息不存在: {}".format(address_id))
            continue

        # 如果改地址管理的设备数目不为0 则不能删除
        if address.device_num > 0:
            log.warn("当前地址关联的设备数不为0，不能删除: address_id = {}".format(address_id))
            continue

        # 判断是否删除成功
        if not address.delete():
            log.warn("地址信息删除失败: {}".format(json.dumps(address.to_dict(), ensure_ascii=False)))
            continue

        result_list.append(address_id)
    return success(result_list)


# 分页获取全部地址列表 [finish]
@bp.route('/address', methods=['POST'])
@login_required
def get_address_list():
    # if not request.is_json:
    #     log.warn("参数错误...")
    #     return fail(HTTP_OK, u"need application/json!!")

    # json = {
    #     'page': 1,
    #     'size': 10,
    # }

    # page = request.json.get('page')
    # size = request.json.get('size')
    #
    # if not isinstance(page, int) or \
    #         not isinstance(size, int):
    #     log.warn("请求参数错误: page = {} size = {}".format(page, size))
    #     return fail(HTTP_OK, u"请求参数错误")
    #
    #     # 请求参数必须为正数
    # if page <= 0 or size <= 0:
    #     msg = "请求参数错误: page = {} size = {}".format(
    #         page, size)
    #     log.error(msg)
    #     return fail(HTTP_OK, msg)
    #
    # if size > 50:
    #     log.info("翻页最大数目只支持50个, 当前size超过50 size = {}!".format(size))
    #     size = 50
    return Address.search_list()


# 通过ID 或者 location 获取地址信息 [finish]
@bp.route('/address/<location>', methods=['GET'])
@login_required
def get_address(location):
    if not isinstance(location, basestring) or location.strip() == '':
        log.warn("传入参数有误: location = {}".format(location))
        return fail(HTTP_OK, u"参数错误!")

    address_list = Address.find_address_by_location(location)
    if len(address_list) > 0:
        return success(address_list)

    try:
        a_id = int(location)
        address = Address.get(a_id)
        if address is not None:
            return success([address.to_dict()])
    except Exception as e:
        log.error("地址信息无法转换为 int 类型: location = {}".format(location))
        log.exception(e)

    return success([])
