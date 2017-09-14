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
from datetime import datetime

from flask import Blueprint
from flask import request
from flask_login import login_required

from exts.common import fail, HTTP_OK, log, success
from service.device.model import Device

bp = Blueprint('device', __name__, url_prefix='/admin')

'''
设备管理需求:
1. 删除设备 [finish]
2. 批量删除设备 [finish]
3. 通过设备ID（mac or 数据库ID）/ 详细地址(不明白是哪个地址)
4. 通过城市区域查找
'''


# 通过城市  区域 获取地址列表
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
    # todo 获取设备信息搜索还未完成
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    page = request.json.get('page')
    size = request.json.get('size')
    city = request.json.get('city')
    area = request.json.get('area')
    start_time_str = request.json.get('start_time')
    end_time_str = request.json.get('end_time')
    state = request.json.get('state')

    if isinstance(start_time_str, basestring) and isinstance(end_time_str, basestring):
        if end_time_str < start_time_str:
            return fail(HTTP_OK, u"时间区间错误: start_time = {} > end_time = {}".format(start_time_str, end_time_str))

    try:
        # 转换为 datetime 类型
        start_time = None
        if isinstance(start_time_str, basestring):
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        else:
            log.info("start_time 不是字符串: {}".format(start_time_str))

        end_time = None
        if isinstance(end_time_str, basestring):
            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        else:
            log.info("end_time 不是字符串: {}".format(end_time_str))

        log.info("转换后时间: start_time = {} type = {}".format(start_time, type(start_time)))
        log.info("转换后时间: end_time = {} type = {}".format(end_time, type(end_time)))
    except Exception as e:
        log.error("时间格式转换错误: start_time_str = {} end_time_str = {}".format(start_time_str, end_time_str))
        log.exception(e)
        return fail(HTTP_OK, u"时间格式转换错误!")

    # if city is None:
    #     log.warn("参数不正确, city字段为None: city = {} area = {}".format(city, area))
    #     return fail(HTTP_OK, u"city字段不能为None")

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

    return success(Device.find_device_list(city, area, start_time, end_time, state, page, size))


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
# @bp.route('/device/list', methods=['POST'])
# @login_required
# def get_device_list():
#     if not request.is_json:
#         log.warn("参数错误...")
#         return fail(HTTP_OK, u"need application/json!!")
#
#     page = request.json.get('page', None)
#     size = request.json.get('size', None)
#     if not isinstance(page, int) or not isinstance(size, int):
#         return fail(HTTP_OK, u"翻页参数错误!")
#
#     if page <= 0 or size <= 0:
#         return fail(HTTP_OK, u"翻页参数错误!")
#
#     return success(Device.get_device_list(page, size))


# 根据设备ID 查找 设备信息
@bp.route('/device/<int:device_id>', methods=['GET'])
@login_required
def get_device_by_id(device_id):
    device = Device.get(device_id)
    if device is None:
        return fail(HTTP_OK, u"设备信息不存在!")

    return success(device.to_dict())
