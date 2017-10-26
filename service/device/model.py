#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: device.py
@time: 2017/8/29 20:59
"""
import json
from datetime import datetime

from exts.common import log, package_result
from exts.model_base import ModelBase
from exts.resource import db
from service.deploy.model import Deploy

__all__ = ['Deploy']


# 设备信息
class Device(ModelBase):
    __tablename__ = 'device'

    # 空闲状态
    STATUE_FREE = 'free'
    # 用户正在使用状态
    STATUE_BUSY = 'busy'
    # 锁定状态: 后台主动锁定，或称 维护状态，锁定状态必须由空闲状态转入，因为busy状态用户正在上机， 维护状态客户端正在操作
    STATUE_LOCK = 'lock'

    # 维护状态 客户端维护人员登录 则进入这个状态
    STATUS_MAINTAIN = 'maintain'

    # 当前设备存活状态
    ALIVE_OFFLINE = 'offline'
    ALIVE_ONLINE = 'online'

    # 游戏更新状态
    UPDATE_WAIT = 'wait'
    UPDATE_FINISH = 'finish'
    UPDATE_ING = 'ing'

    # 使用状态
    STATUS_VALUES = (STATUE_FREE, STATUE_BUSY, STATUE_LOCK, STATUS_MAINTAIN)

    # 更新状态
    UPDATE_STATUS_VALUES = (UPDATE_WAIT, UPDATE_FINISH, UPDATE_ING)

    # 存活状态
    ALIVE_VALUES = (ALIVE_OFFLINE, ALIVE_ONLINE)

    # 设备机器码
    device_code = db.Column(db.String(128), unique=True, index=True)

    # 投放ID
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))

    # 部署记录
    deploy_query = db.relationship('Deploy', backref='device', lazy='dynamic')

    # 设备收入
    income = db.Column(db.Integer, nullable=False, default=0)

    # 设备当前使用状态 free 空闲 busy 忙碌 lock 锁定
    state = db.Column(db.Enum(*STATUS_VALUES), index=True, default=STATUE_FREE)

    # 状态版本信息 乐观锁
    state_version = db.Column(db.Integer, default=0)

    # 存活状态
    alive = db.Column(db.Enum(*ALIVE_VALUES), index=True, default=ALIVE_OFFLINE)

    # 更新状态
    update_state = db.Column(db.Enum(*UPDATE_STATUS_VALUES), default=UPDATE_FINISH)

    # 更新状态版本信息
    update_state_version = db.Column(db.Integer, default=0)

    # 最后更新成功时间
    last_update_time = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return '<Device {}>'.format(self.name)

    # 获得部署列表
    def get_deploy_list(self, page, size):
        # 获取数据总数目
        total = 0
        result_list = list()

        # 获取部署信息列表
        item_paginate = self.deploy_query.paginate(page=page, per_page=size, error_out=False)
        if item_paginate is None:
            log.warn("获取部署信息翻页查询失败: device = {} page = {} size = {}".format(self.id, page, size))
            return package_result(total, result_list)

        item_list = item_paginate.items
        if item_list is None:
            log.warn("部署信息分页查询失败: device = {} page = {} size = {}".format(self.id, page, size))
            return package_result(total, result_list)

        return package_result(item_paginate.total, [item.to_dict() for item in item_list])

    # 删除设备需要事务控制
    def delete(self):
        try:
            db.session.delete(self)
            self.address.device_num -= 1 if self.address.device_num >= 1 else 0
            db.session.add(self.address)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            log.error("未知删除错误: {}".format(json.dumps(self.to_dict(), ensure_ascii=False)))
            log.exception(e)
            return False
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'device_code': self.device_code,
            'address': self.address.to_dict(),
            'income': self.income,
            'state': self.state,
            'alive': self.alive,
            'update_state': self.update_state,
            'last_update_time': self.last_update_time.strftime('%Y-%m-%d %H:%M:%S'),
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }


# 游戏信息管理
class Game(ModelBase):
    __tablename__ = 'game'

    # 设备ID
    device_id = db.Column(db.Integer, index=True, nullable=False)

    # 游戏名称
    name = db.Column(db.String(128), index=True, nullable=False)

    # 当前版本
    current_version = db.Column(db.String(32), nullable=False)

    # 最新版本
    newest_version = db.Column(db.String(32), nullable=False)

    # 是否可以更新
    need_update = db.Column(db.Boolean, default=False)

    # 创建联合索引
    __table_args__ = (
        # 第一句与第二句是同义的，但是第二句需要多加一个参数index=True， UniqueConstraint 唯一性索引创建方式
        # db.UniqueConstraint('province', 'city', 'area', 'location', name='location_index'),
        db.Index('name_index_key', 'device_id', 'name', unique=True),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'name': self.name,
            'current_version': self.current_version,
            'newest_version': self.newest_version,
            'need_update': self.need_update,
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def to_full_dict(self):
        game_dict = self.to_dict()
        device = Device.get(self.device_id)
        if device is None:
            game_dict['device'] = {}
        else:
            game_dict['device'] = device.to_dict()
        return game_dict

    def __repr__(self):
        return '<Game {}>'.format(self.id)
