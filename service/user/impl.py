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


def filter_emoji(des_str, restr=''):
    # 不进行过滤
    log.info("当前需要过滤的用户名: nick_name = {}".format(des_str))
    return des_str
    # log.info("转换前 nick_name = {}".format(des_str))
    # try:
    #     co = re.compile(u'[\U00010000-\U0010ffff]')
    # except re.error:
    #     co = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
    # nick_name = co.sub(restr, des_str)
    # log.info("转换后 nick_name = {}".format(nick_name))
    # return nick_name


class UserService(object):
    @staticmethod
    def create(mobile, openid, nick_name="", head_img_url=""):

        user = User(mobile=mobile,
                    openid=openid,
                    nick_name=filter_emoji(nick_name),
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

    # 存储昵称和头像信息
    @staticmethod
    def save_nick_and_head(user, nick_name, head_img_url):
        if user is None or nick_name is None or head_img_url is None:
            log.error("存储参数异常: user = {} nick_name = {} head_img_url = {}".format(
                user, nick_name, head_img_url))
            return False
        if nick_name == '' and head_img_url == '':
            return False

        if nick_name != '':
            user.nick_name = filter_emoji(nick_name)

        if head_img_url != '':
            user.head_img_url = head_img_url
        return user.save()

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
