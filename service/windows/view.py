#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/20 14:13
"""
import time
from datetime import datetime

from flask import Blueprint
from flask import g
from flask import redirect
from flask import request
from flask import session
from flask import url_for

import settings
from exts.common import fail, HTTP_OK, log, success, LOGIN_ERROR_BIND, LOGIN_ERROR_DELETE, LOGIN_ERROR_FORBID, \
    LOGIN_ERROR_NOT_FIND, LOGIN_ERROR_NOT_SUFFICIENT_FUNDS, LOGIN_ERROR_UNKNOW, LOGIN_ERROR_DEVICE_IN_USING, \
    LOGIN_ERROR_USER_IN_USING, LOGIN_ERROR_DEVICE_NOT_FREE, decode_user_id, ATTENTION_URL
from exts.redis_api import RedisClient
from exts.resource import redis_cache_client
from service.address.model import Address
from service.charge.impl import ChargeService
from service.device.impl import DeviceService, DeviceGameService
from service.device.model import Device, DeviceStatus, DeviceUpdateStatus
from service.maintain.impl import MaintainService
from service.maintain.model import Maintain
from service.windows.impl import WindowsService
from tools.wechat_api import get_current_user, bind_required, get_wechat_user_info

bp = Blueprint('windows', __name__, url_prefix='/windows')


# 扫描上线登录 需要确保微信端已经登录
@bp.route('/login/<device_code>', methods=['GET'])
# @bind_required
def qr_code_online(device_code):
    # # 当前用户没有登录
    # LOGIN_ERROR_BIND = -1
    # # 当前用户已经被删除
    # LOGIN_ERROR_DELETE = -2
    # # 当前用户被禁止使用
    # LOGIN_ERROR_FORBID = -3
    # # 当前设备不存在
    # LOGIN_ERROR_NOT_FIND = -4
    # # 用户余额不足
    # LOGIN_ERROR_NOT_SUFFICIENT_FUNDS = -5
    # # 上线失败 未知错误
    # LOGIN_ERROR_UNKNOW = -6
    # # 设备已经在使用了
    # LOGIN_ERROR_DEVICE_IN_USEING = -7
    # # 当前用户已经在使用上线了，但是不是当前设备在使用
    # LOGIN_ERROR_USER_IN_USEING = -8
    # # 当前设备不处于空闲状态，不能上机
    # LOGIN_ERROR_DEVICE_NOT_FREE = -9

    scan_from = request.args.get('from')
    # 登录链接
    login_url = url_for("wechat.menu", name="login")
    # 通过微信二维码扫描则需要判断当前用户是否已经关注公众号
    if scan_from != 'playing':
        # # 初始化用户关注信息
        # subscribe, nick_name, head_img_url = 0, '', ''

        openid = session.get('openid', None)
        # 如果不是微信二维码扫描 则跳转到登录界面
        if openid is None:
            log.info("当前扫描登录没有openid，需要跳转到登录界面..")
            return redirect(login_url)

        # 获得用户的关注状态 以及头像和昵称信息
        subscribe, nick_name, head_img_url = get_wechat_user_info(openid)
        # 如果用户没有关注微信号 直接跳转到关注页面
        if subscribe != 1:
            log.info("当前用户没有关注公众号: subscribe = {} openid = {}".format(
                subscribe, openid))
            return redirect(ATTENTION_URL)

        # 如果当前用户已经关注 则直接跳转到 祥基指定的链接 2017-10-13 15:26:00
        url = '#/playing?code={}'.format(device_code)
        log.info("当前用户已经关注了公众号，跳转链接: {}".format(url))
        return redirect(url)

    user_id_cookie = session.get('u_id')
    if user_id_cookie is None:
        log.warn("当前session中没有u_id 信息，需要登录...")
        return fail(HTTP_OK, u'当前用户没有登录', LOGIN_ERROR_BIND)

    user_id = decode_user_id(user_id_cookie)
    if user_id is None:
        log.warn("当前用户信息被篡改，需要重新登录: user_id_cookie = {}".format(user_id_cookie))
        return fail(HTTP_OK, u'当前用户登录信息被篡改, 不能登录', LOGIN_ERROR_BIND)

    # 获得用户信息
    user = get_current_user(user_id)
    if user is None:
        log.warn("当前user_id还未绑定手机号码: user_id = {}".format(user_id))
        return fail(HTTP_OK, u"用户还绑定手机号码登录!", LOGIN_ERROR_BIND)

    # 如果当前用户 被禁用 则不能上线
    if user.deleted:
        log.warn("当前用户已经被删除了，不能上线: user_id = {}".format(user.id))
        return fail(HTTP_OK, u"当前用户已经被删除了，不能上机", LOGIN_ERROR_DELETE)

    # 判断当前用户是否已经被禁用了
    if user.state == 'unused':
        log.warn("当前用户已经被禁用了，不能上线: user_id = {}".format(user.id))
        return fail(HTTP_OK, u"当前用户已经被禁用了，不能上线", LOGIN_ERROR_FORBID)

    # 获得设备信息
    device = DeviceService.get_device_by_code(device_code=device_code)
    if device is None:
        log.warn("当前设备号没有对应的设备信息: device_code = {}".format(device_code))
        return fail(HTTP_OK, u"设备信息异常，设备不存在", LOGIN_ERROR_NOT_FIND)

    # 获得最新费率
    charge_mode = ChargeService.get_newest_charge_mode()

    # 判断用户是否余额充足 如果小于一分钟不能上机
    if user.balance_account < charge_mode:
        log.info("用户余额不足，不能上线: user_id = {} device_id = {} account = {}".format(
            user.id, device.id, user.balance_account))
        return fail(HTTP_OK, u"用户余额不足，不能上线!", LOGIN_ERROR_NOT_SUFFICIENT_FUNDS)

    # 判断是否已经在redis中进行记录
    record_key = RedisClient.get_record_key(user.id, device.id)
    # 获得用户上线key
    user_key = RedisClient.get_user_key(user.id)
    # 获得设备上线key
    device_key = RedisClient.get_device_key(device.id)

    # 判断是否已经登录了
    charging = redis_cache_client.get(record_key)
    if charging is None:

        # 判断当前设备是否已经在使用了
        if redis_cache_client.get(device_key):
            log.warn("当前设备{}已经在被使用，但是用户ID = {}又在申请".format(device.id, user.id))
            return fail(HTTP_OK, u"当前设备已经在使用上线了，但是不是当前用户在使用!", LOGIN_ERROR_DEVICE_IN_USING)

        # 判断当前用户是否已经上线了
        if redis_cache_client.get(user_key):
            log.warn("当前用户{}已经在上线，但是又在申请当前设备ID = {}".format(user.id, device.id))
            return fail(HTTP_OK, u"当前用户已经在使用上线了，但是不是当前设备在使用!", LOGIN_ERROR_USER_IN_USING)

        # 判断当前设备是否处于空闲状态 且设备必须处于在线状态
        device_status = DeviceService.get_device_status(device)
        device_alive = DeviceService.get_device_alive_status(device)
        if device_status != DeviceStatus.STATUE_FREE or device_alive != Device.ALIVE_ONLINE:
            log.warn("当前设备不处于空闲状态，不能上机: device_id = {} state = {} alive = {}".format(
                device.id, device_status, device_alive))
            return fail(HTTP_OK, u"当前设备不处于空闲状态，或者当前设备不在线，不能上机!", LOGIN_ERROR_DEVICE_NOT_FREE)

        # 判断当前设备是否正在更新 或者正在自检，这种状态下不能够登录上线
        current_update_state = DeviceService.get_update_state(device)
        if current_update_state == DeviceUpdateStatus.UPDATE_ING or \
                        current_update_state == DeviceUpdateStatus.UPDATE_CHECK:
            log.info("当前设备正在更新或者自检中，不能登录: device_id = {} current_update_state = {}".format(
                device.id, current_update_state))
            return fail(HTTP_OK, u"当前设备处于自检或者更新中，不能上机!", LOGIN_ERROR_DEVICE_NOT_FREE)

        log.info("用户还未上机可以进行上机: user_id = {} device_id = {}".format(user.id, device.id))
        if not WindowsService.do_online(user, device, charge_mode):
            log.warn("上线记录创建失败，上线失败: user_id = {} device_id = {}".format(user.id, device.id))
            return fail(HTTP_OK, u"上机异常!!", LOGIN_ERROR_UNKNOW)

    log.info("来自微信端游戏仓界面扫描: user_id = {} device_id = {}".format(user.id, device.id))
    return success()


@bp.route('/offline', methods=['GET'])
@bind_required
def wechat_offline():
    user_key = RedisClient.get_user_key(g.user_id)
    record_key = redis_cache_client.get(user_key)
    if record_key is None:
        return success({
            'status': 0,
            'msg': "logout failed! reason: user device is already offline"})

    charging = redis_cache_client.get(record_key)
    if charging is None:
        return success({
            'status': 0,
            'msg': "logout failed! reason: user device is already offline"})

    return WindowsService.do_offline(charging)


# 获取用户在线状态
@bp.route('/online/status', methods=['GET'])
@bind_required
def get_online_status():
    user_key = RedisClient.get_user_key(g.user_id)
    record_key = redis_cache_client.get(user_key)
    if record_key is None:
        return fail(HTTP_OK, u'当前用户没有上机信息', 0)

    charging = redis_cache_client.get(record_key)
    if charging is None:
        return fail(HTTP_OK, u'当前用户没有上机信息', 0)

    return success(WindowsService.get_current_time_charging(charging))


# 判断设备是否已经上线登录
@bp.route('/check', methods=['POST'])
def check_connect():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_code = request.json.get('device_code')
    if device_code is None:
        return fail(HTTP_OK, u"not have device_code!!!")

    # 获得设备使用状态
    device_status = DeviceService.get_device_status(device_code)
    if device_status is None:
        return success({
            'status': -1,
            'device_status': device_status,
            'msg': "not deploy"})

    # 保持心跳
    DeviceService.keep_device_heart(device_code)

    # 从维护状态跳转到空闲状态
    if device_status == DeviceStatus.STATUS_MAINTAIN:
        log.info("当前状态为维护状态，设备已经有心跳需要重新设置空闲状态!")
        DeviceService.status_transfer(device_code, device_status, DeviceStatus.STATUE_FREE)

        # 重新获得设备状态
        device_status = DeviceService.get_device_status(device_code)

    device_code_key = RedisClient.get_device_code_key(device_code)
    record_key = redis_cache_client.get(device_code_key)
    if record_key is None:
        return success({
            'status': 0,
            'device_status': device_status,
            'msg': "not login"
        })

    return success({"status": 1,
                    "token": record_key,
                    'device_status': device_status,
                    "msg": "login successed!"})


# 心跳
@bp.route('/keepalive', methods=['POST'])
def keep_alive():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    record_key = request.json.get('token')
    if record_key is None:
        return fail(HTTP_OK, u"not have token!!!")

    device_code = request.json.get('device_code')
    if device_code is None:
        log.error("无法保持心跳, 没有传入device_code: record_key = {}".format(record_key))
        return fail(HTTP_OK, u"not have device_code!!!")

    # 保持心跳
    DeviceService.keep_device_heart(device_code)

    charging = redis_cache_client.get(record_key)
    if charging is None:
        return success({
            "status": 0,
            "msg": "keepalive failed!reason:token invalid"})

    # 获得keep_alive_key 更新最新存活时间
    user_online_key = RedisClient.get_user_online_key(record_key)

    # 设置最新存活时间 最多存在五分钟
    redis_cache_client.setex(user_online_key, settings.MAX_LOST_HEART_TIME, int(time.time()))

    return success({
        "status": 1,
        "msg": "keepalive success",
        "data": WindowsService.get_current_time_charging(charging)})


# Windows端下线，使用的是 user_id#device_id
@bp.route('/logout', methods=['POST'])
def windows_offline():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    token = request.json.get('token')
    if token is None:
        return fail(HTTP_OK, u"not have token!!!")

    charging = redis_cache_client.get(token)
    if charging is None:
        return success({
            'status': 0,
            'msg': "logout failed! reason: user device is already offline"})

    return WindowsService.do_offline(charging)


@bp.route("/maintain/login", methods=['POST'])
def maintain_login():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_code = request.json.get('device_code')
    username = request.json.get('username')
    password = request.json.get('password')

    if device_code is None or username is None or password is None:
        log.error("参数错误，无法登录维修账号: device_code = {} username = {} password = {}".format(
            device_code, username, password))
        return fail(HTTP_OK, u"参数错误!!")

    # 判断维修人员用户密码是否正确
    maintain = MaintainService.get_maintain_by_username(username)
    if maintain is None:
        log.error("当前维修人员账号不存在: username = {} password = {}".format(
            username, password))
        return fail(HTTP_OK, u"当前维修人员账号不存在，维修人员无法登录!!")

    # 判断当前用户是否已经被禁用了
    if maintain.state == Maintain.STATUS_FORBID:
        return fail(HTTP_OK, u"当前账户已被禁用，无法登录!!")

    # 判断密码是否正确
    if not maintain.verify_password(password):
        log.error("当前维护人员密码错误: username = {} password = {}".format(username, password))
        return fail(HTTP_OK, u"密码错误，维修人员无法登录!!")

    # 判断当前设备信息是否存在
    device = DeviceService.get_device_by_code(device_code)
    if device is None:
        log.error("当前设备号没有设备信息: device_code = {}".format(device_code))
        return fail(HTTP_OK, u"当前设备号没有设备信息!!")

    # 判断当前设备存活状态
    if DeviceService.get_device_alive_status(device) == Device.ALIVE_OFFLINE:
        log.error("当前设备离线，维修人员无法登录: device_code = {}".format(device_code))
        return fail(HTTP_OK, u"当前设备离线，维修人员无法登录!!")

    # 判断当前设备使用状态
    if DeviceService.get_device_status(device) == DeviceStatus.STATUE_BUSY:
        log.error("当前设备用户正在使用，维修人员无法登录: device_code = {}".format(device_code))
        return fail(HTTP_OK, u"当前设备用户正在使用，维修人员无法登录!!")

    # 判断当前维护人员账号能否登录当前地址
    if maintain.address_id != Maintain.ALL_ADDRESS_ID:
        address = Address.get(maintain.address_id)
        if address is None:
            log.error("当前维护人员管理的地址信息不存在，无法登录")
            return fail(HTTP_OK, u"当前维护人员管理的地址信息不存在，无法登录!")
        device_address = device.address.get_full_address()
        maintain_address = address.get_full_address()
        if device_address != maintain_address:
            log.error("当前维护人员管理的地址与设备所在地址不一致，无法登录: maintain_id = {} device_id = {}"
                      " device_address = {} maintain_address = {}".format(
                maintain.id, device.id, device_address, maintain_address))
            return fail(HTTP_OK, u"当前维护人员管理的地址与设备所在地址不一致，无法登录!")

    # 开始登录，先设置设备状态
    if not DeviceService.set_device_status(device, DeviceStatus.STATUS_MAINTAIN):
        log.error("设备状态切换错误, 维修人员无法登录: device_code = {} username = {} password = {}".format(
            device_code, username, password))
        return fail(HTTP_OK, u"设备状态切换异常, 维修人员无法登录!")

    log.info("维修人员登录设备成功: device_code = {} username = {} password = {}".format(
        device_code, username, password))
    return success(u"登录成功")


# 获取游戏列表
@bp.route('/game/list', methods=['POST'])
def device_game_list():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_code = request.json.get('device_code')
    device = DeviceService.get_device_by_code(device_code)
    if device is None:
        log.error("当前设备号没有获取到任何设备信息: {}".format(device_code))
        return fail(HTTP_OK, u"参数错误!!")

    # if not isinstance(page, int) or \
    #         not isinstance(size, int):
    #     log.error("获取游戏列表参数错误: page = {} size = {} device_code = {}".format(
    #         page, size, device_code))
    #     return fail(HTTP_OK, u"参数错误!!")
    #
    # if page <= 0 or size <= 0:
    #     log.error("获取游戏列表参数错误, 不能小于0: page = {} size = {} device_code = {}".format(
    #         page, size, device_code))
    #     return fail(HTTP_OK, u"参数错误!!")

    return DeviceGameService.get_device_game_list(device.id)


# 修改游戏更新状态
@bp.route('/game/state', methods=['PUT'])
def modify_device_game_state():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_code = request.json.get('device_code')
    update_state = request.json.get('update_state')

    if update_state not in (DeviceUpdateStatus.UPDATE_ING,
                            DeviceUpdateStatus.UPDATE_FINISH):
        log.error("当前状态不允许: update_state = {}".format(update_state))
        return fail(HTTP_OK, u"参数错误!")

    device = DeviceService.get_device_by_code(device_code)
    if device is None:
        log.error("当前设备号没有获取到任何设备信息: {}".format(device_code))
        return fail(HTTP_OK, u"参数错误,获取设备信息失败!!")

    # 获取当前游戏更新状态
    current_update_state = DeviceService.get_update_state(device)

    # 获取当前设备状态
    current_status = DeviceService.get_device_status(device)

    # 如果当前发送过来的状态是ing 则设备当前游戏更新状态必须是ing，否则状态错误
    if update_state == DeviceUpdateStatus.UPDATE_ING:
        if current_update_state == DeviceUpdateStatus.UPDATE_CHECK:
            return fail(HTTP_OK, u"当前游戏更新状态错误, 自检中不接收ing状态")

        # 锁定设备
        if current_status != DeviceStatus.STATUE_FREE and \
                        current_status != DeviceStatus.STATUE_LOCK:
            return fail(HTTP_OK, u"当前设备不为空闲或者锁定状态，无法更新!")

        # 如果当前设备为空闲状态 则锁定设备
        if current_status == DeviceStatus.STATUE_FREE:
            if not DeviceService.set_device_status(device, DeviceStatus.STATUE_LOCK):
                log.error("锁定设备失败，设置设备状态信息失败: device_id = {}".format(device.id))
                return fail(HTTP_OK, u'锁定设备失败，设置设备状态信息失败!!')

        if DeviceService.set_update_state(device, update_state):
            return success(u"设备游戏更新状态设置成功!")
        return fail(HTTP_OK, u"更新状态设置失败")

    # 判断当前属于什么状态
    if current_update_state == DeviceUpdateStatus.UPDATE_FINISH:
        return success(u'当前属于游戏更新完成状态，不需要设置')

    # 如果当前设备被锁定了 则解锁
    if current_status == DeviceStatus.STATUE_LOCK:
        if not DeviceService.set_device_status(device, DeviceStatus.STATUE_FREE):
            log.error("解锁设备异常: device_id = {}".format(device.id))
            return fail(HTTP_OK, u'设备解锁失败，多进程写入设备状态异常!')

    # 如果当前属于更新中状态
    if current_update_state == DeviceUpdateStatus.UPDATE_ING:
        # 设置游戏更新完成。。
        DeviceGameService.update_device_game(device_id=device.id)
        if DeviceService.set_update_state(device, update_state, last_update_time=datetime.now()):
            return success(u"设备游戏更新状态设置成功!")
        return fail(HTTP_OK, u"更新状态设置失败")

    if DeviceService.set_update_state(device, update_state):
        return success(u"设备游戏更新状态设置成功!")
    return fail(HTTP_OK, u"更新状态设置失败")

    # if update_state == DeviceUpdateStatus.UPDATE_ING:
    #     # 锁定设备
    #     if current_status != DeviceStatus.STATUE_FREE and \
    #                     current_status != DeviceStatus.STATUE_LOCK:
    #         return fail(HTTP_OK, u"当前设备不为空闲或者锁定状态，无法更新!")
    #
    #     # 如果当前设备为空闲状态 则锁定设备
    #     if current_status == DeviceStatus.STATUE_FREE:
    #         if not DeviceService.set_device_status(device, DeviceStatus.STATUE_LOCK):
    #             log.error("锁定设备失败，设置设备状态信息失败: device_id = {}".format(device.id))
    #             return fail(HTTP_OK, u'锁定设备失败，设置设备状态信息失败!!')
    #
    #     if DeviceService.set_update_state(device, update_state):
    #         return success(u"设备游戏更新状态设置成功!")
    #     return fail(HTTP_OK, u"更新状态设置失败")

    # 如果当前设备状态不为ing 则不进行更新设置
    # if DeviceService.get_update_state(device) != DeviceUpdateStatus.UPDATE_ING:
    #     return success(u'当前状态不正确, 不能设置')
    #
    # # 如果当前设备被锁定了 则解锁
    # if current_status == DeviceStatus.STATUE_LOCK:
    #     if not DeviceService.set_device_status(device, DeviceStatus.STATUE_FREE):
    #         log.error("解锁设备异常: device_id = {}".format(device.id))
    #         return fail(HTTP_OK, u'设备解锁失败，多进程写入设备状态异常!')
    #
    # # 设置游戏更新完成。。
    # DeviceGameService.update_device_game(device_id=device.id)
    # if DeviceService.set_update_state(device, update_state, last_update_time=datetime.now()):
    #     return success(u"设备游戏更新状态设置成功!")
    # return fail(HTTP_OK, u"更新状态设置失败")


# 获取游戏更新状态
@bp.route('/game/state', methods=['POST'])
def get_device_game_state():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_code = request.json.get('device_code')
    if not isinstance(device_code, basestring):
        return fail(HTTP_OK, u"参数类型错误!")

    update_state = DeviceService.get_update_state(device_code)
    if update_state is None:
        log.error("当前设备号没有获取到任何设备信息: {}".format(device_code))
        return fail(HTTP_OK, u'当前设备号信息不正确，无法获取更新状态信息')

    return success(update_state)
