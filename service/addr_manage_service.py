#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: addr_manage_service.py
@time: 2017/8/30 21:26
"""

# 地址操作接口
import common
from common import log
from model.addr_manage import AddrManage


class AddrMangeService(object):
    # 数据不存在
    CODE_NOT_EXIST = -3

    # 数据存储异常
    CODE_ERROR = -2

    # 数据已经存在
    CODE_ALREADY_EXIST = -1

    # 成功
    CODE_SUCCESS = 0

    # 数据不存在
    MSG_NOT_EXIST = "数据不存在"

    # 数据存储异常
    MSG_ERROR = "数据存储异常"

    # 数据已经存在
    MSG_ALREADY_EXIST = "地址信息已经存在"

    # 成功
    MSG_SUCCESS = "success"

    def __init__(self, db):
        self.db = db

    # 插入新地址
    def insert(self, address):
        # 先判断地址是否已经存在
        item = AddrManage.query.filter_by(address=address).first()
        if item is not None:
            log.warn("当前地址信息已经存在: {}".format(address))
            return common.get_response(self.CODE_ALREADY_EXIST, self.MSG_ALREADY_EXIST)
        try:
            addr = AddrManage(address, 0)
            self.db.session.add(addr)
            self.db.session.commit()
            return common.get_response(self.CODE_SUCCESS, self.MSG_SUCCESS, data=addr.id)
        except Exception as e:
            log.error("地址信息存储异常: {}".format(address))
            log.exception(e)

        return common.get_response(self.CODE_ERROR, self.MSG_ERROR)

    # 删除地址信息
    def delete(self, address_id):
        # 先判断id是否存在
        item = AddrManage.query.filter_by(id=address_id).first()
        if item is None:
            return common.get_response(self.CODE_NOT_EXIST, self.MSG_NOT_EXIST)

        # 删除数据
        try:
            self.db.session.delete(item)
            self.db.session.commit()
            return common.get_response(self.CODE_SUCCESS, self.MSG_SUCCESS, data=item.id)
        except Exception as e:
            log.error("地址数据删除失败: {}".format(address_id))
            log.exception(e)
        return common.get_response(self.CODE_ERROR, self.MSG_ERROR)

    # 增加设备数目
    def update(self, address_id, dev_num):
        # 先判断id是否存在
        item = AddrManage.query.filter_by(id=address_id).first()
        if item is None:
            return common.get_response(self.CODE_NOT_EXIST, self.MSG_NOT_EXIST)

        try:
            item.device_num += dev_num
            item.update()
            self.db.session.commit()
            return common.get_response(self.CODE_SUCCESS, self.MSG_SUCCESS, data=item.id)
        except Exception as e:
            log.error("更新数据失败: {} {} type = {}".format(address_id, dev_num, type(dev_num)))
            log.exception(e)

        return common.get_response(self.CODE_ERROR, self.MSG_ERROR)
