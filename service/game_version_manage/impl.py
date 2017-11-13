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
from service.game_version_manage.model import GameVersionManage, GameList


class GameVersionManageService(object):
    @staticmethod
    def create(game, version, md5):

        try:
            game_manage = GameVersionManage(game=game,
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
    def update_game_info(game_manage, md5):
        game_manage.md5 = md5
        return game_manage.save()

    @staticmethod
    def delete_game(game):
        try:
            game_list = GameVersionManage.query.filter_by(game=game).all()
            [db.session.delete(game_item) for game_item in game_list]
            db.session.commit()
        except Exception as e:
            log.error("删除游戏失败:")
            log.exception(e)
            return False
        return True

    @staticmethod
    def get_game_info(game, version):
        return GameVersionManage.query.filter_by(game=game, version=version).first()


# 游戏列表操作接口
class GameListService(object):
    # 更新游戏接口
    @staticmethod
    def update_game_list(game, version):
        try:
            game_list = GameList.query.filter_by(game=game).first()
            if game_list is not None:
                game_list.version = version
                return game_list.save()

            try:
                game_list = GameList(game=game,
                                     version=version)
                db.session.add(game_list)
                db.session.commit()
                return True
            except IntegrityError:
                log.error("主键重复: game = {} version = {}".format(
                    game, version))
                db.session.rollback()

        except Exception as e:
            log.error("游戏列表更新失败:")
            log.exception(e)

        return False

    # 从游戏列表中删除游戏
    @staticmethod
    def delete_game_list(game):
        try:
            game_list = GameList.query.filter_by(game=game).first()
            if game_list is not None:
                db.session.delete(game_list)
                db.session.commit()
        except Exception as e:
            log.error("删除游戏失败:")
            log.exception(e)

    # 获得游戏列表
    @staticmethod
    def get_game_list():

        result_list = []
        try:
            game_list = GameList.query.all()

            for game_item in game_list:
                result_list.append([game_item.game, game_item.version])
        except Exception as e:
            log.error("获取最新游戏列表失败:")
            log.exception(e)
        return result_list
