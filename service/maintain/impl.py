#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/10/24 10:10
"""
from datetime import datetime

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

    @staticmethod
    def to_address_dict(item):
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
        return item_dict

    # 获取维护人员列表信息
    @staticmethod
    def search_list():

        log.info("获取维护人员列表信息...")
        total, item_list = Maintain.search_item_list()
        if total <= 0 or item_list is None:
            return success(package_result(0, []))

        result_list = []
        for item in item_list:
            # item_dict = item.to_dict()
            # while True:
            #
            #     # 判断是否所有大厅
            #     if item.address_id == Maintain.ALL_ADDRESS_ID:
            #         full_address = Maintain.ALL_ADDRESS_STR
            #         break
            #
            #     # 获取地址信息
            #     address = Address.get(item.address_id)
            #     if address is None:
            #         log.warn("当前地址不存在: maintain_id = {} address_id = {}".format(item.id, item.address_id))
            #         full_address = '当前地址不存在!'
            #         break
            #
            #     full_address = address.get_full_address()
            #     break
            #
            # item_dict['address'] = full_address
            result_list.append(MaintainService.to_address_dict(item))

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
        if isinstance(name, basestring) and name.strip() != "":
            update_info[Maintain.name] = name.strip()
        if isinstance(password, basestring) and password.strip() != "":
            update_info[Maintain.hashed_password] = Maintain.generate_password(password.strip())
        if isinstance(address_id, int):
            update_info[Maintain.address_id] = address_id

        update_info[Maintain.utime] = datetime.now()

        rowcount = Maintain.query.filter_by(id=maintain_id).update(update_info)
        # 不确定是否需要commit
        # db.session.commit()
        if rowcount <= 0:
            log.warn("更新失败: rowcount = {}".format(rowcount))
            return False

        # 更新
        log.info("维护人员信息更新成功: maintain_id = {} rowcount = {}".format(maintain_id, rowcount))
        return True

    @staticmethod
    def get_maintain_by_username(username):
        return Maintain.query.filter_by(username=username).first()

    # 校验密码是否正确
    @staticmethod
    def verify_password(username, password):
        result = u'登录成功!'
        maintain = MaintainService.get_maintain_by_username(username)
        if maintain is None:
            result = u'账户不存在!'
            log.error("当前维护人员ID没有找到相关信息: username = {}".format(username))
            return False, result
        is_success = maintain.verify_password(password)
        if is_success:
            log.info("当前维护人员登录成功: username = {} password = {}".format(username, password))
        else:
            result = u'密码错误!'
            log.warn("当前维护人员密码错误: username = {} password = {}".format(username, password))
        return is_success, result

    @staticmethod
    def delete_maintain(maintain_id):
        maintain = Maintain.get(maintain_id)
        if maintain is None:
            log.error("当前维护人员不存在: maintain_id = {}".format(maintain_id))
            return False

        if not maintain.delete():
            log.error("当前维护人员删除失败: maintain_id = {}".format(maintain_id))
            return False

        log.error("当前维护人员删除成功: maintain_id = {}".format(maintain_id))
        return True

    # 设置维护人员状态
    @staticmethod
    def state_maintain(maintain_id, state):

        maintain = Maintain.get(maintain_id)
        if maintain is None:
            log.error("当前ID没有找到对应的维护人员信息: maintain_id = {}".format(maintain_id))
            return False

        maintain.state = state
        is_success = maintain.save()
        if not is_success:
            log.error("维护人员状态修改失败: maintain_id = {} state = {}".format(maintain_id, maintain.state))
        else:
            log.info("维护人员状态修改成功: maintain_id = {} state = {}".format(maintain_id, maintain.state))

        return is_success

    @staticmethod
    def find_list(keyword):
        query = Maintain.query

        # 先通过ID查找
        try:
            maintain_id = int(keyword)
            total = query.filter(Maintain.id == maintain_id).count()
            if total > 0:
                return total, query.filter(Maintain.id == maintain_id).all()
        except Exception as e:
            log.warn("通过ID查找失败: keyword = {}".format(keyword))
            log.exception(e)

        # 再通过用户名查找
        total = query.filter(Maintain.username == keyword).count()
        if total > 0:
            return total, query.filter(Maintain.username == keyword).all()

        # 再通过姓名查找
        total = query.filter(Maintain.name == keyword).count()
        if total > 0:
            return total, query.filter(Maintain.name == keyword).all()

        return 0, []

    # 通过关键字搜索维护人员信息
    @staticmethod
    def search_by_keyword(keyword):
        total, item_list = MaintainService.find_list(keyword)
        if total <= 0 or not isinstance(item_list, list):
            return success(package_result(0, []))

        return success(package_result(total, [MaintainService.to_address_dict(item) for item in item_list]))
