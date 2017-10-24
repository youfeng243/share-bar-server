#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/10/24 10:10
"""
from sqlalchemy.exc import IntegrityError

from exts.common import log, package_result, success
from exts.resource import db
from service.address.model import Address
from service.maintain.model import Maintain


# 维护人员接口
class MaintainService(object):
    # 创建维护人员
    @staticmethod
    def create(username, password, name, address_id=Maintain.ALL_ADDRESS_ID):

        # 如果地址信息不正确，则选用所有地址可用
        if Address.get(address_id) is None:
            log.warn("当前传入地址ID没有找到相应地址信息，默认调整为全部地区: address_id = {}".format(address_id))

            address_id = Maintain.ALL_ADDRESS_ID

        maintain = Maintain(
            username=username,
            name=name,
            address_id=address_id)
        maintain.password = password

        try:
            db.session.add(maintain)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: username = {} name = {} address_id = {}".format(
                username, name, address_id))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: username = {} name = {} address_id = {}".format(
                username, name, address_id))
            log.exception(e)
            return None, False
        return maintain, True

    # 获取维护人员列表信息
    @staticmethod
    def search_list():

        log.info("获取维护人员列表信息...")
        total, item_list = Maintain.search_item_list()
        if total <= 0 or item_list is None:
            return success(package_result(0, []))

        result_list = []
        for item in item_list:
            item_dict = item.to_dict()
            while True:

                # 判断是否所有大厅
                if item.address_id == Maintain.ALL_ADDRESS_ID:
                    full_address = Maintain.ALL_ADDRESS_STR
                    break

                # 获取地址信息
                address = Address.get(item.address_id)
                if address is None:
                    log.warn("当前地址不存在: maintain_id = {} address_id = {}".format(item.id, item.address_id))
                    full_address = '当前地址不存在!'
                    break

                full_address = address.get_full_address()
                break

            item_dict['address'] = full_address
            result_list.append(item_dict)

        return success(package_result(total, result_list))

    # 修改维护人员信息
    @staticmethod
    def update_maintain(maintain_id, name=None, password=None, address_id=None):
        if name is None and password is None and address_id is None:
            log.info("维护人员没有任何信息需要更新...")
            return True

        # 如果地址信息不正确，则选用所有地址可用
        if address_id is not None and Address.get(address_id) is None:
            log.warn("当前传入地址ID没有找到相应地址信息，默认调整为全部地区: address_id = {}".format(address_id))
            address_id = Maintain.ALL_ADDRESS_ID

        # maintain = Maintain.get(maintain_id)
        # if maintain is None:
        #     log.error("传入的id没有找到维护人员信息: maintain_id = {}".format(maintain_id))
        #     return False

        update_info = {}
        if name is not None:
            update_info['name'] = name
        if password is not None:
            update_info['password'] = password
        if address_id is not None:
            update_info['address_id'] = address_id

        rowcount = Maintain.query.filter_by(id == maintain_id).update(update_info)
        # 不确定是否需要commit
        # db.session.commit()
        if rowcount <= 0:
            log.warn("更新失败: rowcount = {}".format(rowcount))
            return False

        log.info("维护人员信息更新成功: maintain_id = {} rowcount = {}".format(maintain_id, rowcount))
        return True
