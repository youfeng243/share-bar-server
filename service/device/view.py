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
from service.device.model import Device
from service.use_record.model import UseRecord

bp = Blueprint('device', __name__, url_prefix='/admin')

'''
设备管理需求:
1. 删除设备 [finish]
2. 批量删除设备 [finish]
3. 通过设备ID（mac or 数据库ID）/ 详细地址(不明白是哪个地址) [目前采用简单的ID或者设备mac进行查询]
4. 通过城市区域时间等复合查询 [finish]
'''


# 通过城市  区域 时间 区间 状态获取地址列表
@bp.route('/device/list', methods=['POST'])
@login_required
def get_device_list():
    '''
    page: 当前页码
    size: 每页读取数目, 最大不超过50项
    city: 查询的城市 如不传或者为None则查询全部城市
    area: 查询城市所属区域，如不传或者为None则查询该城市全部区域，前置条件必须有城市信息
    start_time: 查询的起始时间段 时间段其实时间必须小于或者等于end_time
    end_time: 查询的结束时间段 时间段必须大于或者等于start_time
    state: 当前设备状态 如 为None 则查询所有状态
    :return:
    '''

    return Device.search_list()


# # 删除设备
# @bp.route('/device/<int:device_id>', methods=['DELETE'])
# @login_required
# def delete_device(device_id):
#     device = Device.get(device_id)
#     if device is None:
#         log.warn("当前设备ID查找设备失败: {}".format(device_id))
#         return fail(HTTP_OK, u"设备不存在")
#
#     if not device.delete():
#         log.warn("设备信息删除失败: {}".format(json.dumps(device.to_dict(), ensure_ascii=False)))
#         return fail(HTTP_OK, u"删除设备信息失败!")
#
#     return success(device.id)


# 批量删除设备
@bp.route('/device', methods=['DELETE'])
@login_required
def delete_devices():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    id_list = request.json.get('list', None)
    if not isinstance(id_list, list):
        log.warn("参数错误: id_list = {}".format(id_list))
        return fail(HTTP_OK, u"传入不是id列表")

    result_list = []
    for device_id in id_list:
        device = Device.get(device_id)
        if device is None:
            log.warn("当前ID设备信息不存在: {}".format(device_id))
            continue

        if not device.delete():
            log.warn("设备信息删除失败: {}".format(json.dumps(device.to_dict(), ensure_ascii=False)))
            continue

        result_list.append(device_id)
    return success(result_list)


# 根据设备ID 查找 设备信息
@bp.route('/device/<device_id>', methods=['GET'])
@login_required
def get_device_by_id(device_id):
    # 先通过设备mac地址查找
    device = Device.get_device_by_code(device_id)
    if device is not None:
        return success(device.to_dict())

    try:
        a_id = int(device_id)
        device = Device.get(a_id)
        if device is not None:
            return success(device.to_dict())
    except Exception as e:
        log.error("设备信息无法转换为 int 类型: device_id = {}".format(device_id))
        log.exception(e)

    return success(None)


# 通过城市  区域 时间 区间 状态获取地址列表
@bp.route('/device/records', methods=['POST'])
@login_required
def get_device_use_records():
    '''
    page: 当前页码
    size: 每页读取数目, 最大不超过50项
    start_time: 查询的起始时间段 时间段其实时间必须小于或者等于end_time
    end_time: 查询的结束时间段 时间段必须大于或者等于start_time
    :return:
    '''
    # {
    #     "page": 1,
    #
    #     "size": 10,
    #     "device_id": 100
    # }
    return UseRecord.search_list()
