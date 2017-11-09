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

from exts.common import fail, HTTP_OK, log, success, is_valid_time
from exts.resource import redis_cache_client
from service.admin.impl import AdminService
from service.device.impl import DeviceService, GameService
from service.device.model import Device, DeviceStatus
from service.use_record.model import UseRecord
from service.windows.impl import WindowsService

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
    return DeviceService.search_list()


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


@bp.route('/device/lock', methods=['POST'])
@login_required
def lock_device():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_id = request.json.get('id')
    lock = request.json.get('lock')

    if device_id is None or lock is None:
        log.error("传入参数不正确: id = {} lock = {}".format(device_id, lock))
        return fail(HTTP_OK, u"传入参数错误!")

    # 获得设备信息
    device = DeviceService.get_device_by_id(device_id)
    if device is None:
        log.error("当前设备ID没有找到设备信息: device_id = {}".format(device_id))
        return fail(HTTP_OK, u"当前设备ID没有找到设备信息!")

    # 获取当前设备存活状态
    alive = DeviceService.get_device_alive_status(device)
    if alive == Device.ALIVE_OFFLINE:
        log.info("当前设备不在线，无法锁定设备: device_id = {} alive = {}".format(device_id, alive))
        return fail(HTTP_OK, u"当前设备不在线，无法锁定设备!")

    # 获取设备当前使用状态
    use_status = DeviceService.get_device_status(device)
    if use_status is None:
        log.error("获取当前设备状态错误, 无法操作设备: device_id = {}".format(device_id))
        return fail(HTTP_OK, u'获取当前设备状态错误, 无法操作设备')

    # 当前是否是想解锁设备
    if not lock:
        if use_status == DeviceStatus.STATUE_LOCK:
            if not DeviceService.set_device_status(device, DeviceStatus.STATUE_FREE):
                return fail(HTTP_OK, u'设备解锁失败，多进程写入设备状态异常!')
            log.info("解锁设备成功: device_id = {} device_code = {}".format(device.id, device.device_code))
            return success(u'解锁设备成功')
        return success(u'当前设备未锁定，不需要解锁!')

    # 判断设备是否处于维护状态
    if use_status == DeviceStatus.STATUS_MAINTAIN:
        log.info("当前设备维护人员已登录，无法锁定设备: device_id = {} use_status = {}".format(device_id, use_status))
        return fail(HTTP_OK, u"当前设备维护人员已登录，无法锁定设备!")

    if use_status == DeviceStatus.STATUE_LOCK:
        log.info("当前设备已被锁定，不需要再锁定: device_id = {} use_status = {}".format(device_id, use_status))
        return success(u"当前设备已被锁定，不需要再锁定")

    # 当前设备处于忙碌状态，锁定设备
    if use_status == DeviceStatus.STATUE_BUSY:
        log.info("当前设备有用户在使用，强制用户下机，锁定设备: device_id = {} use_status = {}".format(device_id, use_status))
        if not WindowsService.do_offline_order_by_device_code(device.device_code):
            return fail(HTTP_OK, u"强制用户下机失败，无法锁定设备!")

        if not DeviceService.set_device_status(device, DeviceStatus.STATUE_LOCK):
            log.error("锁定设备失败，设置设备状态信息失败: device_id = {}".format(device_id))
            return fail(HTTP_OK, u'锁定设备失败，设置设备状态信息失败!!')
        log.info("锁定设备成功: device_id = {} device_code = {}".format(device.id, device.device_code))
        return success(u'当前设备有用户在使用，强制用户下机，锁定设备成功')

    if not DeviceService.set_device_status(device, DeviceStatus.STATUE_LOCK):
        log.error("锁定设备失败，设置设备状态信息失败: device_id = {}".format(device_id))
        return fail(HTTP_OK, u'锁定设备失败，设置设备状态信息失败!!')
    log.info("锁定设备成功: device_id = {} device_code = {}".format(device.id, device.device_code))
    return success(u'锁定设备成功')


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
            device = DeviceService.get_device_by_id(a_id)
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


# 获取游戏列表
@bp.route('/device/game/list', methods=['POST'])
@login_required
def device_game_list():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    page = request.json.get('page')
    size = request.json.get('size')
    device_id = request.json.get('device_id')

    if not isinstance(page, int) or \
            not isinstance(size, int) or \
            not isinstance(device_id, int):
        log.error("获取游戏列表参数错误: page = {} size = {} device_id = {}".format(
            page, size, device_id))
        return fail(HTTP_OK, u"参数错误!!")

    if page <= 0 or size <= 0:
        log.error("获取游戏列表参数错误, 不能小于0: page = {} size = {} device_id = {}".format(
            page, size, device_id))
        return fail(HTTP_OK, u"参数错误!!")

    return GameService.get_device_game_list(device_id, page, size)


# 设备游戏管理列表
@bp.route('/device/game/manage', methods=['POST'])
@login_required
def get_device_game_manage():
    '''
    page: 当前页码
    size: 每页读取数目, 最大不超过50项
    :return:
    '''

    return DeviceService.search_list()


# 更新游戏
@bp.route('/device/game/update', methods=['POST'])
@login_required
def device_game_update():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_id = request.json.get('device_id')
    is_all = request.json.get('all')

    if device_id is None and is_all is None:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"参数错误, device_id or all 必须有一个!")

    log.info("当前设备更新参数为: device_id = {} is_all = {}".format(device_id, is_all))
    if is_all:
        if GameService.update_all():
            log.info("所有设备游戏更新状态设置成功!")
            return success(u"设备游戏更新状态设置成功!")
        return fail(HTTP_OK, u"游戏更新设置失败，请重试!")

    if GameService.update(device_id):
        log.info("设备游戏更新状态设置成功: device_id = {}".format(device_id))
        return success(u"设备游戏更新状态设置成功!")

    return fail(HTTP_OK, u"设备设置游戏更新失败!")


# 判断设备是否需要更新
@bp.route('/device/need/update', methods=['POST'])
@login_required
def device_need_update():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_id = request.json.get('device_id')

    if device_id is None:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"参数错误!")

    return success(GameService.is_device_need_update(device_id))


# 更新游戏
@bp.route('/backdoor/update/game', methods=['GET'])
def backdoor_game_update():
    if GameService.update_all():
        log.info("所有设备游戏更新状态设置成功!")
        return success(u"设备游戏更新状态设置成功!")
    return fail(HTTP_OK, u"游戏更新设置失败，请重试!")


# 设置更新当前时间
@bp.route('/device/game/time', methods=['PUT'])
@login_required
def modify_game_update_time():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    time_str = request.json.get('time')
    if time_str is None:
        log.error("修改时间参数错误: time = None")
        return fail(HTTP_OK, u"参数错误")

    # 判断时间格式是否正确
    if not is_valid_time(time_str):
        log.error("时间格式错误: time = {}".format(time_str))
        return fail(HTTP_OK, u"时间格式错误: %H:%M:%S")

    # 设置时间
    GameService.set_game_update_time(time_str, redis_cache_client)
    return success(u"时间更新成功!")


# 获得设备游戏更新时间
@bp.route('/device/game/time', methods=['GET'])
@login_required
def get_game_update_time():
    return success(GameService.get_game_update_time(redis_cache_client))


# 添加游戏 或者更新游戏版本
@bp.route('/device/game', methods=['POST'])
def device_game_add():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    username = request.json.get('username')
    password = request.json.get('password')
    name = request.json.get('game')
    version = request.json.get('version')

    if not isinstance(name, basestring) or not isinstance(version, basestring):
        log.error("参数错误: username = {} password = {} game = {} version = {}".format(
            username, password, name, version))
        return fail(HTTP_OK, u"参数错误")

    # 先判断能否登录
    is_success, msg = AdminService.verify_authentication(username, password)
    if not is_success:
        return fail(HTTP_OK, msg)

    # 开始更新游戏信息
    if not GameService.add_device_game(name, version):
        return fail(HTTP_OK, u"游戏更新失败，请重试!")

    return success(u'游戏更新成功!')


# 添加游戏 或者更新游戏版本
@bp.route('/device/game', methods=['DELETE'])
def device_game_delete():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    username = request.json.get('username')
    password = request.json.get('password')
    name = request.json.get('game')

    if not isinstance(name, basestring):
        log.error("参数错误: username = {} password = {} game = {}".format(
            username, password, name))
        return fail(HTTP_OK, u"参数错误")

    # 先判断能否登录
    is_success, msg = AdminService.verify_authentication(username, password)
    if not is_success:
        return fail(HTTP_OK, msg)

    # 开始更新游戏信息
    if not GameService.delete_device_game(name):
        return fail(HTTP_OK, u"游戏删除失败，请重试!")

    return success(u'游戏删除成功!')
