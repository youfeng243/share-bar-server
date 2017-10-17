#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/10/16 21:26
"""
from flask import url_for

from exts.common import WECHAT_ACCESS_TOKEN_KEY, log
from exts.resource import redis
from service.template.wechat_template import WechatTemplate


class TemplateService(object):
    # 获得access_token
    # @classmethod
    # def get_access_token(cls):
    #     access_token = redis.get(WECHAT_ACCESS_TOKEN_KEY)
    #     if access_token is None:
    #         log.error("access_token 为None，刷新token进程异常！！！")
    #         return subscribe, nick_name, head_img_url

    # 上机提醒
    @classmethod
    def online(cls, openid,
               # 上线时间 self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
               ctime,
               # 地址 结构体对象
               address,
               # 余额 分
               balance,
               # 计费 价格 分钟 / 分
               charge_mode):
        access_token = redis.get(WECHAT_ACCESS_TOKEN_KEY)
        if access_token is None:
            log.error("access_token 为None，刷新token进程异常！！！")
            return
        online_time = ctime.strftime('%Y-%m-%d %H:%M:%S')
        address_str = address.province + address.city + address.area + address.location

        account_url = url_for("wechat.menu", name="account", _external=True)
        log.info("当前用户中心地址: url = {}".format(account_url))
        if WechatTemplate.online(access_token, openid, online_time, address_str, balance, charge_mode, url=account_url):
            log.info("发送微信上机通知成功: openid = {}".format(openid))
        else:
            log.warn("发送微信上机通知失败: openid = {}".format(openid))

    # 下机提醒
    @classmethod
    def offline(cls, openid,
                record,
                # 余额 分
                balance):

        access_token = redis.get(WECHAT_ACCESS_TOKEN_KEY)
        if access_token is None:
            log.error("access_token 为None，刷新token进程异常！！！")
            return
        offline_time = record.end_time.strftime('%Y-%m-%d %H:%M:%S')
        address_str = record.province + record.city + record.area + record.location
        if WechatTemplate.offline(access_token, openid, offline_time, address_str, balance, record.cost_time):
            log.info("发送微信下机通知成功: openid = {}".format(openid))
        else:
            log.warn("发送微信下机通知失败: openid = {}".format(openid))

    # 充值提醒
    @classmethod
    def recharge_remind(cls, openid, pay_time, account):
        access_token = redis.get(WECHAT_ACCESS_TOKEN_KEY)
        if access_token is None:
            log.error("access_token 为None，刷新token进程异常！！！")
            return

        recharge_time = pay_time.strftime('%Y-%m-%d %H:%M:%S')
        if WechatTemplate.recharge_remind(access_token, openid, recharge_time, account):
            log.info("发送微信充值通知成功: openid = {}".format(openid))
        else:
            log.warn("发送微信充值通知失败: openid = {}".format(openid))
