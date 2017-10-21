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

    # 使用状态
    STATUS_VALUES = (STATUE_FREE, STATUE_BUSY, STATUE_LOCK, STATUS_MAINTAIN)

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

    # 存活状态
    alive = db.Column(db.Enum(*ALIVE_VALUES), index=True, default=ALIVE_OFFLINE)

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
            'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
        }
