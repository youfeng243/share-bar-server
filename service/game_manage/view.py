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

from exts.common import log, HTTP_OK, fail, success
from service.device.impl import GameService
from service.game_manage.impl import GameManageService

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

    game_manage, is_success = GameManageService.create(game, version, md5)
    if not is_success:
        return fail(HTTP_OK, u"游戏更新失败，请重试!")

    # 开始更新游戏信息
    if not GameService.add_device_game(game, version):
        return fail(HTTP_OK, u"游戏更新失败，请重试!")

    return success(u'游戏更新成功!')


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

    result = GameManageService.get_game_info(game, version)
    if result is None:
        return fail(HTTP_OK, u'没有当前游戏版本记录')

    return success(result)
