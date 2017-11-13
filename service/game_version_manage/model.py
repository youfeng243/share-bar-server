#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: admin_manage.py
@time: 2017/8/30 09:10
"""

from exts.model_base import ModelBase
from exts.resource import db


# 游戏版本管理信息
class GameVersionManage(ModelBase):
    __tablename__ = 'game_version_manage'

    # 游戏名称
    game = db.Column(db.String(256), index=True, nullable=False)

    # 游戏版本
    version = db.Column(db.String(32), nullable=False)

    # 游戏文件的 md5
    md5 = db.Column(db.String(128), nullable=False)

    # 创建联合索引
    __table_args__ = (
        # 第一句与第二句是同义的，但是第二句需要多加一个参数index=True， UniqueConstraint 唯一性索引创建方式
        db.Index('game_index_key', 'game', 'version', unique=True),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'game': self.game,
            'version': self.version,
            'md5': self.md5,
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }


# 游戏列表管理信息，存储最新游戏版本
class GameList(ModelBase):
    __tablename__ = 'game_list'

    # 游戏名称
    game = db.Column(db.String(256), index=True, nullable=False)

    # 游戏版本
    version = db.Column(db.String(32), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'game': self.game,
            'version': self.version,
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }
