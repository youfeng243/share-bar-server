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
import time

import redis
import requests

import settings
from logger import Logger

log = Logger('process_access_token.log').get_logger()

try:
    redis_client = redis.StrictRedis.from_url(settings.REDIS_URI, max_connections=32)
except Exception as e:
    log.error("启动redis失败..")
    log.exception(e)
    exit(0)

# 在redis中的key
ACCESS_TOKEN_KEY = "global:access_token"

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
        redis_client.setex(ACCESS_TOKEN_KEY, expires_in, access_token)
    except Exception as e:
        log.error("访问token链接失败:")
        log.exception(e)

    return False


def main():
    log.info("开始启动access_token刷新进程...")
    # 30秒轮询一次
    SLEEP_TIME = 30
    while True:
        try:
            value = redis_client.ttl(ACCESS_TOKEN_KEY)
            if value <= LAST_TIME:
                log.info("开始获取token...")
                update_access_token()
                log.info("获取token结束...")

        except Exception as e:
            log.error("程序异常:")
            log.exception(e)
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()
