#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: service.py
@time: 2017/9/25 00:14
"""
from sqlalchemy.exc import IntegrityError

from exts.common import log
from exts.database import db
from service.user.model import User


class UserService(object):
    @staticmethod
    def create(mobile, openid, nick_name="", head_img_url=""):
        user = User(mobile=mobile,
                    openid=openid,
                    nick_name=nick_name,
                    head_img_url=head_img_url)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: mobile = {}".format(mobile))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: mobile = {}".format(mobile))
            log.exception(e)
            return None, False
        return user, True

    # 根据用户ID 获得用户信息
    @staticmethod
    def get_by_id(user_id):
        return User.get(user_id)

    # 根据微信ID 获取用户信息
    @staticmethod
    def get_by_openid(openid):
        return User.query.filter_by(openid=openid).first()

    # 根据手机号码查找用户信息
    @staticmethod
    def get_user_by_mobile(mobile):
        return User.query.filter_by(mobile=mobile).first()
