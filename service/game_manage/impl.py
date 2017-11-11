#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/11/11 10:44
"""
from sqlalchemy.exc import IntegrityError

from exts.common import log
from exts.resource import db
from service.game_manage.model import GameManage


class GameManageService(object):
    @staticmethod
    def create(game, version, md5):

        try:
            game_manage = GameManage(game=game,
                                     version=version,
                                     md5=md5)
            db.session.add(game_manage)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: game = {} version = {} md5 = {}".format(
                game, version, md5))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: game = {} version = {} md5 = {}".format(
                game, version, md5))
            log.exception(e)
            return None, False
        return game_manage, True

    @staticmethod
    def get_game_info(game, version):
        item = GameManage.query.filter_by(game=game, version=version).first()
        if item is None:
            return None
        return item.to_dict()
