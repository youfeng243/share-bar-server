#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/9 15:08
"""
from flask import Blueprint
from flask import request
from flask_login import login_required

from exts.common import log, fail, HTTP_OK, success
from service.address.model import Address
from service.deploy.model import Deploy
from service.device.model import Device

bp = Blueprint('deploy', __name__, url_prefix='/admin')


# 部署设备
@bp.route('/deploy', methods=['POST'])
@login_required
def deploy_device():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    province = request.json.get('province', None)
    city = request.json.get('city', None)
    area = request.json.get('area', None)
    location = request.json.get('location', None)
    if province is None or city is None \
            or area is None or location is None \
            or province == '' or city == '' \
            or area == '' or location == '':
        log.warn("地址信息传入错误: province = {} city = {} area = {} location = {}".format(
            province, city, area, location))
        return fail(HTTP_OK, u"地址信息传入错误!")

    # 获得设备编号信息
    device_code = request.json.get('device_code', None)
    if device_code is None:
        log.warn("没有设备编号信息无法部署...")
        return fail(HTTP_OK, u"没有设备编号信息无法部署!")

    # 先获得地址信息 通过地址四个属性进行查找
    address = Address.find_address(province, city, area, location)
    if address is None:
        # 如果地址信息不存在则创建地址但是设备数要先初始化为0
        address, is_success = Address.create(province, city, area, location, device_num=0)
        if address is None:
            log.warn("部署设备时地址信息创建失败了: province = {} city = {} area = {} location = {} device_code = {}".format(
                province, city, area, location, device_code))
            return fail(HTTP_OK, u"新建地址信息失败了!")

    # 先判断设备是否已经存在设备列表中
    device = Device.get_device_by_code(device_code)
    if device is None:
        # 如果没有找到设备信息则新建设备信息
        device, is_success = Device.create(device_code, address.id)
        if device is None:
            log.warn("新建设备信息失败了!!")
            return fail(HTTP_OK, u"新建设备信息失败了!")
        address.add_device_num(1)

    # 添加部署记录 先判断当前部署的位置是否和设备当前所处的位置是一样的
    if device.address_id == address.id:
        log.info("当前设备部署的位置没有发生任何变化，不需要记录: {} {}".format(
            device.id, address.id))
        return success()

    # 先获得之前部署的位置
    address_old = Address.get(device.address_id)
    if address_old.device_num > 0:
        address_old.add_device_num(-1)

    # 然后更改部署的位置
    device.address_id = address.id
    address.add_device_num(1)

    # 增加部署记录
    deploy, is_success = Deploy.create(device.id, province, city, area, location)
    if deploy is None:
        log.warn("添加部署记录失败!")
        return fail(HTTP_OK, u"添加部署记录失败!")

    return success(deploy.to_dict())


# 获得部署记录列表
@bp.route('/deploy/list', methods=['POST'])
@login_required
def get_deploy_list():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    page = request.json.get('page', None)
    size = request.json.get('size', None)
    if not isinstance(page, int) or not isinstance(size, int):
        return fail(HTTP_OK, u"翻页参数错误!")

    if page <= 0 or size <= 0:
        return fail(HTTP_OK, u"翻页参数错误!")

    device_id = request.json.get('id', None)
    if device_id is None:
        return fail(HTTP_OK, u"没有设备ID信息，无法获取设备记录")

    # 查找对应的设备
    device = Device.get(device_id)
    if device is None:
        return fail(HTTP_OK, u"没有对应的设备信息...")

    # 返回记录列表信息
    return success(device.get_deploy_list(page, size))
