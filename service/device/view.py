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

# 添加地址 [finish] 根据 20170908与张雅晴确认 新地址通过部署添加，而不是手动添加地址接口暂不对外提供
# @bp.route('/address', methods=['POST'])
# @login_required
# def new_address():
#     if not request.is_json:
#         log.warn("参数错误...")
#         return fail(HTTP_OK, u"need application/json!!")
#
#     province = request.json.get('province', None)
#     city = request.json.get('city', None)
#     area = request.json.get('area', None)
#     location = request.json.get('location', None)
#     if province is None or city is None \
#             or area is None or location is None \
#             or province == '' or city == '' \
#             or area == '' or location == '':
#         log.warn("地址信息传入错误: province = {} city = {} area = {} location = {}".format(
#             province, city, area, location))
#         return fail(HTTP_OK, u"地址信息传入错误!")
#
#     # 查找地址是否已经存在
#     if Address.find_address(province, city, area, location) is not None:
#         log.warn("地址信息已存在: province = {} city = {} area = {} location = {}".format(
#             province, city, area, location))
#         return fail(HTTP_OK, u"地址信息已存在!")
#
#     address = Address.create(province, city, area, location)
#     return success(address.to_dict())


# # 删除地址 [finish]
# @bp.route('/address', methods=['DELETE'])
# @login_required
# def delete_address():
#     if not request.is_json:
#         log.warn("参数错误...")
#         return fail(HTTP_OK, u"need application/json!!")
#
#     a_id = request.json.get('id', None)
#     if a_id is None:
#         log.warn("传入参数错误: addr_id = {} ".format(a_id))
#         return fail(HTTP_OK, u"传入参数错误!")
#
#     # 查找地址是否已经存在
#     address = Address.get(a_id)
#     if address is None:
#         log.warn("地址信息不存在: {}".format(a_id))
#         return fail(HTTP_OK, u"地址信息不存在!")
#
#     # 如果改地址管理的设备数目不为0 则不能删除
#     if address.device_num > 0:
#         return fail(HTTP_OK, u"与该地址关联的设备数目不为0")
#
#     address.delete()
#     return success()
#
#
# # 分页获取全部地址列表 [finish]
# @bp.route('/address', methods=['POST'])
# @login_required
# def get_address_list():
#     if not request.is_json:
#         log.warn("参数错误...")
#         return fail(HTTP_OK, u"need application/json!!")
#
#     # json = {
#     #     'page': 1,
#     #     'size': 10,
#     # }
#
#     page = request.json.get('page')
#     size = request.json.get('size')
#
#     if not isinstance(page, int) or \
#             not isinstance(size, int):
#         log.warn("请求参数错误: page = {} size = {}".format(page, size))
#         return fail(HTTP_OK, u"请求参数错误")
#
#         # 请求参数必须为正数
#     if page <= 0 or size <= 0:
#         msg = "请求参数错误: page = {} size = {}".format(
#             page, size)
#         log.error(msg)
#         return fail(HTTP_OK, msg)
#
#     return success(Address.get_address_list(page, size))
#
#
# # 通过ID 或者 location 获取地址信息 [finish]
# @bp.route('/address/<location>', methods=['GET'])
# @login_required
# def get_address(location):
#     if not isinstance(location, basestring) or location.strip() == '':
#         log.warn("传入参数有误: location = {}".format(location))
#         return fail(HTTP_OK, u"参数错误!")
#
#     address_list = Address.find_address_by_location(location)
#     if len(address_list) > 0:
#         return success(address_list)
#
#     try:
#         a_id = int(location)
#         address = Address.get(a_id)
#         if address is not None:
#             return success([address.to_dict()])
#     except Exception as e:
#         log.error("地址信息无法转换为 int 类型: location = {}".format(location))
#         log.exception(e)
#
#     return success([])
#
#
# # 通过城市  区域 获取地址列表
# @bp.route('/address/area', methods=['POST'])
# @login_required
# def get_address_by_area():
#     if not request.is_json:
#         log.warn("参数错误...")
#         return fail(HTTP_OK, u"need application/json!!")
#
#     page = request.json.get('page')
#     size = request.json.get('size')
#     city = request.json.get('city', None)
#     area = request.json.get('area', None)
#     if city is None:
#         log.warn("参数不正确, city字段为None: city = {} area = {}".format(city, area))
#         return fail(HTTP_OK, u"city字段不能为None")
#
#     if not isinstance(page, int) or \
#             not isinstance(size, int):
#         log.warn("请求参数错误: page = {} size = {}".format(page, size))
#         return fail(HTTP_OK, u"请求参数错误")
#
#         # 请求参数必须为正数
#     if page <= 0 or size <= 0:
#         msg = "请求参数错误: page = {} size = {}".format(
#             page, size)
#         log.error(msg)
#         return fail(HTTP_OK, msg)
#
#     return success(Address.find_address_by_city_and_area(city, area, page, size))
#
#
# # 通过起始结束创建时间获取 地址列表
# @bp.route('/address/time', methods=['POST'])
# @login_required
# def get_address_by_time():
#     if not request.is_json:
#         log.warn("参数错误...")
#         return fail(HTTP_OK, u"need application/json!!")
#
#     page = request.json.get('page')
#     size = request.json.get('size')
#     start_time_str = request.json.get('start_time', None)
#     end_time_str = request.json.get('end_time', None)
#     if start_time_str is None or end_time_str is None:
#         log.warn("参数不正确, 字段为None: start_time = {} end_time = {}".format(start_time_str, end_time_str))
#         return fail(HTTP_OK, u"字段不能为None")
#
#     try:
#         # 转换为 datetime 类型
#         start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%I:%S')
#         end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%I:%S')
#         log.info("转换后时间: start_time = {} type = {}".format(start_time, type(start_time)))
#         log.info("转换后时间: end_time = {} type = {}".format(end_time, type(end_time)))
#     except Exception as e:
#         log.error("时间格式转换错误: start_time_str = {} end_time_str = {}".format(start_time_str, end_time_str))
#         log.exception(e)
#         return fail(HTTP_OK, u"时间格式转换错误!")
#
#     if not isinstance(page, int) or \
#             not isinstance(size, int):
#         log.warn("请求参数错误: page = {} size = {}".format(page, size))
#         return fail(HTTP_OK, u"请求参数错误")
#
#         # 请求参数必须为正数
#     if page <= 0 or size <= 0:
#         msg = "请求参数错误: page = {} size = {}".format(
#             page, size)
#         log.error(msg)
#         return fail(HTTP_OK, msg)
#
#     return success(Address.find_address_by_time(start_time, end_time, page, size))
