#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/10/27 17:48
"""
from service.admin.model import Admin


class AdminService(object):
    @staticmethod
    def verify_authentication(username, password):
        admin = Admin.get_by_username(username)
        if admin is None:
            return False, u"用户名不存在!"

        if not admin.verify_password(password):
            return False, u'密码错误'

        return True, u'登录成功'
