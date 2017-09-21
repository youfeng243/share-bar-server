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

    a_id = request.json.get('id', None)
    if a_id is None:
        log.warn("传入参数错误: addr_id = {} ".format(a_id))
        return fail(HTTP_OK, u"传入参数错误!")

    # 查找地址是否已经存在
    address = Address.get(a_id)
    if address is None:
        log.warn("地址信息不存在: {}".format(a_id))
        return fail(HTTP_OK, u"地址信息不存在!")

    # 如果改地址管理的设备数目不为0 则不能删除
    if address.device_num > 0:
        return fail(HTTP_OK, u"与该地址关联的设备数目不为0")

    # 判断是否删除成功
    if not address.delete():
        log.warn("地址信息删除失败: {}".format(json.dumps(address.to_dict(), ensure_ascii=False)))
        return fail(HTTP_OK, u"删除地址信息失败!")
    return success(address.to_dict())


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
