#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: access_token_process.py
@time: 2017/9/25 15:28
"""
import json
import threading
import time

import redis
import requests

import settings
from logger import Logger

log = Logger('process_weixin_cache.log').get_logger()

try:
    redis_client = redis.StrictRedis.from_url(settings.REDIS_URI, max_connections=32)
except Exception as e:
    log.error("启动redis失败..")
    log.exception(e)
    exit(0)

# 最后剩余阈值
LAST_TIME = 300


def update_access_token():
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}'.format(
        settings.WECHAT_APP_ID, settings.WECHAT_APP_SECRET)
    try:
        resp = requests.get(url, verify=False, timeout=30)
        if resp.status_code != 200:
            log.error("访问状态码不正确: status_code = {}".format(resp.status_code))
            return False

        json_data = json.loads(resp.text)
        access_token = json_data.get('access_token')
        expires_in = json_data.get('expires_in')
        if not isinstance(access_token, basestring) or not isinstance(expires_in, int):
            log.error("解析出来的数据类型不正确: {}".format(resp.text))
            return False

        if expires_in <= 0:
            log.error("过期时间不正确: {}".format(expires_in))
            return False

        log.info("成功获取token: access_token = {} expires_in = {}".format(access_token, expires_in))

        # 设置redis
        redis_client.setex(settings.WECHAT_ACCESS_TOKEN_KEY, expires_in, access_token)

        return True
    except Exception as e:
        log.error("访问token链接失败:")
        log.exception(e)

    return False


def update_ticket():
    access_token = redis_client.get(settings.WECHAT_ACCESS_TOKEN_KEY)
    url = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={}&type=jsapi'.format(access_token)

    try:
        resp = requests.get(url, verify=False, timeout=30)
        if resp.status_code != 200:
            log.error("ticket访问状态码不正确: status_code = {}".format(resp.status_code))
            return False

        json_data = json.loads(resp.text)
        errcode = json_data.get('errcode')
        if errcode != 0:
            log.error("更新jsapi_ticket错误码不正确: {}".format(resp.text))
            return False

        ticket = json_data.get('ticket')
        expires_in = json_data.get('expires_in')
        if not isinstance(ticket, basestring) or not isinstance(expires_in, int):
            log.error("ticket解析出来的数据类型不正确: {}".format(resp.text))
            return False

        if expires_in <= 0:
            log.error("ticket过期时间不正确: {}".format(expires_in))
            return False

        log.info("成功获取ticket: ticket = {} expires_in = {}".format(ticket, expires_in))

        # 设置redis
        redis_client.setex(settings.WECHAT_JSAPI_TICKET_KEY, expires_in, ticket)

        return True
    except Exception as e:
        log.error("访问ticket链接失败:")
        log.exception(e)
    return False


def access_token_thread():
    log.info("开始启动缓存刷新线程...")
    # 30秒轮询一次
    SLEEP_TIME = 30
    while True:
        try:
            ttl = redis_client.ttl(settings.WECHAT_ACCESS_TOKEN_KEY)
            log.info("当前key存活时间: key = {} ttl = {}".format(settings.WECHAT_ACCESS_TOKEN_KEY, ttl))
            if ttl <= LAST_TIME:
                log.info("开始获取token...")
                update_access_token()
                log.info("获取token结束...")

            ttl = redis_client.ttl(settings.WECHAT_JSAPI_TICKET_KEY)
            log.info("当前key存活时间: key = {} ttl = {}".format(settings.WECHAT_JSAPI_TICKET_KEY, ttl))
            if ttl <= LAST_TIME:
                log.info("开始获取jsapi_ticket...")
                update_ticket()
                log.info("获取jsapi_ticket结束...")

        except Exception as e:
            log.error("缓存程序异常:")
            log.exception(e)
        time.sleep(SLEEP_TIME)


# 启动计费线程
def charging_thread():
    log.info("开始启动计费线程...")

    SLEEP_TIME = 60
    while True:
        try:
            pass

        except Exception as e:
            log.error("计费线程异常:")
            log.exception(e)
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    # 刷新微信缓存线程
    access_token_handler = threading.Thread(target=access_token_thread)
    access_token_handler.start()

    # 刷新上线扣费线程
    charging_handler = threading.Thread(target=charging_thread)
    charging_handler.start()

    access_token_handler.join()
    charging_handler.join()
