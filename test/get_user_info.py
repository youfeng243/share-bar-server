#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: get_user_info.py
@time: 2017/10/15 18:51
"""

# 获得用户的关注状态 以及头像和昵称信息
import json
import sys

import requests

sys.path.append("..")
from exts.common import WECHAT_ACCESS_TOKEN_KEY
from exts.redis_api import RedisClient
from logger import Logger

log = Logger('get_user_info.log').get_logger()
redis_client = RedisClient()


def get_wechat_user_info(openid):
    # 默认设置是未关注状态
    subscribe, nick_name, head_img_url = 0, '', ''

    if openid is None:
        log.error("openid 为None，未知异常！！！")
        return subscribe, nick_name, head_img_url

    access_token = redis_client.get(WECHAT_ACCESS_TOKEN_KEY)
    if access_token is None:
        log.error("access_token 为None，刷新token进程异常！！！")
        return subscribe, nick_name, head_img_url

    url = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token={}&openid={}&lang=zh_CN'.format(
        access_token, openid)
    try:
        resp = requests.get(url, verify=False, timeout=30)
        if resp.status_code != 200:
            log.error("获取用户信息访问状态码不正确: status_code = {} url = {}".format(
                resp.status_code, url))
            return subscribe, nick_name, head_img_url

        json_data = json.loads(resp.text)
        errcode = json_data.get('errcode')
        if errcode is not None:
            log.error("获取用户信息错误码不正常: {}".format(resp.text))
            return subscribe, nick_name, head_img_url

        subscribe = json_data.get('subscribe')
        if subscribe is None:
            log.error("获取用户信息关注状态不正常: {}".format(resp.text))
            return 0, nick_name, head_img_url

        # 如果用户关注了 才去获取昵称和头像信息
        if subscribe == 1:
            # 获得用户昵称 和头像信息
            nick_name = json_data.get('nickname')
            head_img_url = json_data.get('headimgurl')
            log.info("当前用户关注了公众号, 能够获取昵称和头像: openid = {} nick_name = {} head_img_url = {}".format(
                openid, nick_name, head_img_url))

            # ticket = json_data.get('ticket')
            # expires_in = json_data.get('expires_in')
            # if not isinstance(ticket, basestring) or not isinstance(expires_in, int):
            #     log.error("ticket解析出来的数据类型不正确: {}".format(resp.text))
            #     return False
            #
            # if expires_in <= 0:
            #     log.error("ticket过期时间不正确: {}".format(expires_in))
            #     return False
            #
            # log.info("成功获取ticket: ticket = {} expires_in = {}".format(ticket, expires_in))
            #
            # # 设置redis
            # redis_client.setex(WECHAT_JSAPI_TICKET_KEY, expires_in, ticket)

            # return True
    except Exception as e:
        log.error("访问微信用户链接失败: url = {}".format(url))
        log.exception(e)
    return subscribe, nick_name, head_img_url


if __name__ == '__main__':
    print get_wechat_user_info('oU6SZ0rHqeAKqFWWN3mnDkjDGkdc')
