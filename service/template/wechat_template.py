#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: wechat_template.py
@time: 2017/10/16 18:07
"""

# 微信模板接口
import json

import requests

from exts.common import log


class WechatTemplate(object):
    TEMPLATE_URL = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token='

    # 上机模板
    TEMPLATE_ONLINE = '-7GVci4NkcCYqJ1qc7pdK7DlirfKh4D4DjNARdmVPZw'

    # 下机模板
    TEMPLATE_OFFLINE = 'WZoGrzZ42zOxzZ-ZjZK7RhqnT8VYVfHNGJzGDtlzEKw'

    # 充值成功模板
    TEMPLATE_RECHARGE = 'TMMhtpUbO4XRyNRZNVAEENwFskpkZcKesvZlSvsnc9w'

    def __init__(self):
        pass

    @classmethod
    def get_time(cls, minutes):
        day = minutes // (24 * 60)
        hour = (minutes % (24 * 60)) // 60
        minute = minutes % 60
        return "{:0>2}天{:0>2}小时{:0>2}分钟".format(day, hour, minute)

    @classmethod
    def get_online_time(cls, balance, charge_mode):
        '''
        00天10小时00分钟
        :param balance: 余额
        :param charge_mode: 费率
        :return:
        '''

        if charge_mode <= 0:
            return "00天00小时00分钟"

        minutes = balance // charge_mode

        return cls.get_time(minutes)

        # day = minutes // (24 * 60)
        # hour = (minutes % (24 * 60)) // 60
        # minute = minutes % 60
        #
        # return "{:0>2}天{:0>2}小时{:0>2}分钟".format(day, hour, minute)

    # 上机提醒
    @classmethod
    def online(cls, access_token, openid,
               # 上线时间 字符串 self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
               online_time,
               # 地址 字符串
               address,
               # 余额 分
               balance,
               # 计费 价格 分钟 / 分
               charge_mode,
               url=''):

        data = {
            "first": {
                "value": "上机成功",
            },
            "keyword1": {
                "value": online_time,
            },
            "keyword2": {
                "value": address,
            },
            "keyword3": {
                "value": "{}元".format(balance / 100.0)
            },
            "keyword4": {
                "value": cls.get_online_time(balance, charge_mode)
            },
            "remark": {
                "value": "祝您游戏愉快!",
            }
        }

        return cls.send_wechat_template(access_token, cls.TEMPLATE_ONLINE, openid, data, url)

    # 下机提醒
    @classmethod
    def offline(cls, access_token, openid,
                # 下机时间 字符串 self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
                offline_time,
                # 地址 字符串
                address,
                # 余额 分
                balance,
                # 本次上机花费时间  分
                cost_time):
        data = {
            "first": {
                "value": "下机成功",
            },
            "keyword1": {
                "value": offline_time,
            },
            "keyword2": {
                "value": address,
            },
            "keyword3": {
                "value": "{}元".format(balance / 100.0)
            },
            "keyword4": {
                "value": cls.get_time(cost_time)
            },
            "remark": {
                "value": "感谢您的使用!",
            }
        }

        return cls.send_wechat_template(access_token, cls.TEMPLATE_OFFLINE, openid, data)

    # 充值提醒
    @classmethod
    def recharge_remind(cls, access_token, openid, recharge_time, account):
        data = {
            "first": {
                "value": "账户充值成功",
            },
            "keyword1": {
                "value": "{}元".format(account / 100.0),
            },
            "keyword2": {
                "value": recharge_time,
            },
            "remark": {
                "value": "感谢您的使用!",
            }
        }

        return cls.send_wechat_template(access_token, cls.TEMPLATE_OFFLINE, openid, data)

    @classmethod
    def send_wechat_template(cls, access_token, template_id, openid, data, url=''):
        post_url = cls.TEMPLATE_URL + access_token
        json_data = {
            "touser": openid,
            "template_id": template_id,
            "data": data
        }
        if url != '':
            json_data['url'] = url

        try:
            result = requests.post(post_url, json=json_data)
            if result.status_code != 200:
                log.error("发送模板消息失败: openid = {} data = {}".format(openid, json.dumps(data, ensure_ascii=False)))
                return False

            log.info("发送模板消息result = {}".format(result.text))
        except Exception as e:
            log.error("发送模板消息失败:")
            log.exception(e)
            return False

        return True
