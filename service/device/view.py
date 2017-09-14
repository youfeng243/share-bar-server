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

bp = Blueprint('device', __name__, url_prefix='/admin')


# 删除设备
@bp.route('/device/<int:device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id):
    device = Device.get(device_id)
    if device is None:
        log.warn("当前设备ID查找设备失败: {}".format(device_id))
        return fail(HTTP_OK, u"设备不存在")

    if not device.delete():
        log.warn("设备信息删除失败: {}".format(json.dumps(device.to_dict(), ensure_ascii=False)))
        return fail(HTTP_OK, u"删除设备信息失败!")
    return success(device.to_dict())


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


# 获取设备列表信息
@bp.route('/device/list', methods=['POST'])
@login_required
def get_device_list():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    page = request.json.get('page', None)
    size = request.json.get('size', None)
    if not isinstance(page, int) or not isinstance(size, int):
        return fail(HTTP_OK, u"翻页参数错误!")

    if page <= 0 or size <= 0:
        return fail(HTTP_OK, u"翻页参数错误!")

    return success(Device.get_device_list(page, size))


# 根据设备ID 查找 设备信息
@bp.route('/device/<int:device_id>', methods=['GET'])
@login_required
def get_device_by_id(device_id):
    device = Device.get(device_id)
    if device is None:
        return fail(HTTP_OK, u"设备信息不存在!")

    return success(device.to_dict())