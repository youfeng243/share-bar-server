#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/7 20:32
"""

from flask import Blueprint
from flask import request
from flask_login import login_required

from exts.common import fail, HTTP_OK, log, success
from service.device.impl import DeviceService
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

    # 同步设备存活状态到mysql中
    DeviceService.sync_device_alive_status()
    return Device.search_list()


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
        if not DeviceService.delete_device(device_id):
            log.warn("当前设备删除失败: device_id = {}".format(device_id))
            continue

        result_list.append(device_id)
    return success(result_list)


# 根据设备ID 查找 设备信息
@bp.route('/device/<device_id>', methods=['GET'])
@login_required
def get_device_by_id(device_id):
    device = None
    while True:
        try:

            # 先通过设备mac地址查找
            device = DeviceService.get_device_by_code(device_id)
            if device is not None:
                break

            a_id = int(device_id)
            device = Device.get(a_id)
        except Exception as e:
            log.error("设备信息无法转换为 int 类型: device_id = {}".format(device_id))
            log.exception(e)
        break

    if device is None:
        return success(None)

    # 获取设备最新存活状态
    device.alive = DeviceService.get_device_alive_status(device.device_code)
    return success(device.to_dict())


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
