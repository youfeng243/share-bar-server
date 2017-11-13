#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/11/11 10:55
"""

from flask import Blueprint
from flask import request

import settings
from exts import common
from exts.common import log, HTTP_OK, fail, success
from exts.resource import mongodb
from service.device.impl import DeviceGameService
from service.game_version_manage.impl import GameVersionManageService, GameListService

bp = Blueprint('game_manage', __name__, url_prefix='/game_manage')


# 添加游戏 或者更新游戏版本
@bp.route('/update', methods=['POST'])
def update_game():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    game = request.json.get('game')
    version = request.json.get('version')
    md5 = request.json.get('md5')

    if not isinstance(game, basestring) or \
            not isinstance(version, basestring) or \
            not isinstance(md5, basestring):
        log.error("参数错误:  game = {} version = {} md5 = {}".format(
            game, version, md5))
        return fail(HTTP_OK, u"参数错误")

    # 更新游戏列表
    if not GameListService.update_game_list(game, version):
        return fail(HTTP_OK, u"更新游戏列表失败!")

    game_manage = GameVersionManageService.get_game_info(game, version)
    if game_manage is None:
        game_manage, is_success = GameVersionManageService.create(game, version, md5)
        if not is_success:
            return fail(HTTP_OK, u"游戏更新失败，请重试!")
    else:
        if not GameVersionManageService.update_game_info(game_manage, md5):
            return fail(HTTP_OK, u"游戏更新失败，请重试!")

    # 开始更新游戏信息
    if not DeviceGameService.add_device_game(game, version):
        return fail(HTTP_OK, u"游戏更新失败，请重试!")

    return success(u'游戏更新成功!')


@bp.route('/update', methods=['DELETE'])
def delete_game():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    game = request.json.get('game')
    if not isinstance(game, basestring):
        log.error("参数错误:  game = {}".format(
            game))
        return fail(HTTP_OK, u"参数错误")

        # game_manage = GameVersionManageService.get_game_info(game, version)
        # if game_manage is None:
        #     game_manage, is_success = GameVersionManageService.create(game, version, md5)
        #     if not is_success:
        #         return fail(HTTP_OK, u"游戏更新失败，请重试!")
        # else:
        #     if not GameVersionManageService.update_game_info(game_manage, md5):
        #         return fail(HTTP_OK, u"游戏更新失败，请重试!")
        #
        # # 开始更新游戏信息
        # if not DeviceGameService.add_device_game(game, version):
        #     return fail(HTTP_OK, u"游戏更新失败，请重试!")
        #
        # return success(u'游戏更新成功!')

    # 从游戏列表中删除游戏
    GameListService.delete_game_list(game)

    # 开始删除游戏信息
    DeviceGameService.delete_device_game(game)

    # 开始删除游戏列表信息
    if not GameVersionManageService.delete_game(game):
        return fail(HTTP_OK, u"游戏删除失败，请重试!")

    return success(u'游戏删除成功!')


# 获取游戏信息
@bp.route('/md5', methods=['POST'])
def get_game_md5():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    game = request.json.get('game')
    version = request.json.get('version')
    if not isinstance(game, basestring) or \
            not isinstance(version, basestring):
        log.error("参数错误:  game = {} version = {}".format(
            game, version))
        return fail(HTTP_OK, u"参数错误")

    game_manage = GameVersionManageService.get_game_info(game, version)
    if game_manage is None:
        return fail(HTTP_OK, u'没有当前游戏版本记录')

    return success(game_manage.to_dict())


@bp.route('/log', methods=['POST'])
def upload_game_log():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    device_code = request.json.get('device_code')
    text = request.json.get('text')
    if not isinstance(device_code, basestring) or \
            not isinstance(text, basestring):
        log.error("参数错误:  device_code = {} text = {}".format(
            device_code, text))
        return fail(HTTP_OK, u"参数错误")
    try:
        mongodb.insert(settings.MONGO_LOG_TABLE, {
            'in_time': common.get_now_time(),
            'text': text,
            'device_code': device_code,
        })
    except Exception as e:
        log.error("插入日志信息失败:")
        log.exception(e)

    return success('success')
