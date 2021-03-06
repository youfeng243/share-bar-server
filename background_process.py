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

import requests
from apscheduler.schedulers.background import BackgroundScheduler

import settings
from exts.common import WECHAT_ACCESS_TOKEN_KEY, WECHAT_JSAPI_TICKET_KEY, REDIS_PRE_RECORD_KEY, log, cal_cost_time, \
    DEFAULT_GAME_UPDATE_TIME
from exts.redis_api import RedisClient
from service.device.impl import DeviceGameService
from service.windows.impl import WindowsService

try:
    cache_client = RedisClient(db=0)
except Exception as ex:
    log.error("启动redis失败..")
    log.exception(ex)
    exit(0)

# 最后剩余时间阈值
WX_CACHE_LAST_TIME = 300


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
        cache_client.setex(WECHAT_ACCESS_TOKEN_KEY, expires_in, access_token)

        return True
    except Exception as e:
        log.error("访问token链接失败:")
        log.exception(e)

    return False


def update_ticket():
    access_token = cache_client.get(WECHAT_ACCESS_TOKEN_KEY)
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
        cache_client.setex(WECHAT_JSAPI_TICKET_KEY, expires_in, ticket)

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
            ttl = cache_client.ttl(WECHAT_ACCESS_TOKEN_KEY)
            log.info("当前key存活时间: key = {} ttl = {}".format(WECHAT_ACCESS_TOKEN_KEY, ttl))
            if ttl <= WX_CACHE_LAST_TIME:
                log.info("开始获取token...")
                update_access_token()
                log.info("获取token结束...")

            ttl = cache_client.ttl(WECHAT_JSAPI_TICKET_KEY)
            log.info("当前key存活时间: key = {} ttl = {}".format(WECHAT_JSAPI_TICKET_KEY, ttl))
            if ttl <= WX_CACHE_LAST_TIME:
                log.info("开始获取jsapi_ticket...")
                update_ticket()
                log.info("获取jsapi_ticket结束...")

        except Exception as e:
            log.error("缓存程序异常:")
            log.exception(e)
        time.sleep(SLEEP_TIME)


def do_charging(record_key_list):
    if not isinstance(record_key_list, list):
        log.error("当前传入参数不正确: type = {}".format(type(record_key_list)))
        return

    if len(record_key_list) <= 0:
        log.info("当前没有上线用户，不需要计费...")
        return

    # 开始针对用户进行扣费
    for record_key in record_key_list:

        charge_str = cache_client.get(record_key)
        if charge_str is None:
            log.info("当前用户已经下线，不需要再计费: record_key = {}".format(record_key))
            continue

        try:
            charge_dict = json.loads(charge_str)

            user_id = charge_dict.get('user_id')
            if user_id is None:
                log.error("没有关键信息 user_id: charge_str = {}".format(charge_str))
                continue

            device_id = charge_dict.get('device_id')
            if device_id is None:
                log.error("没有关键信息 device_id: charge_str = {}".format(charge_str))
                continue

            record_key = RedisClient.get_record_key(user_id, device_id)

            # 判断是否已经有5分钟没有收到心跳
            user_online_key = RedisClient.get_user_online_key(record_key)
            last_timestamp = cache_client.get(user_online_key)
            if last_timestamp is None:
                log.info("没有收到任何心跳信息, 强制下机, 当前上线用户没有最后存活时间: user_id = {} device_id = {}".format(
                    user_id, device_id))
                # 执行下机流程
                if WindowsService.do_offline_order(record_key):
                    log.info("没有收到任何心跳信息,强制下机完成: record_key = {}".format(record_key))
                else:
                    log.error("强制下机失败: record_key = {}".format(record_key))
                continue

            # # 获得当前时间戳
            # last_timestamp = int(last_timestamp)
            # now_timestamp = int(time.time())
            #
            # # 如果当前丢失心跳的时间超过阈值，则默认离线，需要下机
            # if now_timestamp - last_timestamp >= settings.MAX_LOST_HEART_TIME:
            #     # 下机
            #     log.info("当前用户与机器没有收到任何心跳信息，强制下机: record_key = {} last_timestamp = {}".format(
            #         record_key, last_timestamp))
            #     # 执行下机流程
            #     do_offline_order(record_key)
            #     log.info("没有收到任何心跳信息,强制下机完成: record_key = {}".format(record_key))
            #     continue

            # charge_dict = {
            #     'id': self.id,
            #     'user_id': self.user_id,
            #     'device_id': self.device_id,
            #     # 花费金额数目
            #     'cost_money': self.cost_money,
            #     # 上机时间
            #     'ctime': self.ctime.strftime('%Y-%m-%d %H:%M:%S'),
            #     # 更新时间，主要用户同步计费
            #     'utime': self.utime.strftime('%Y-%m-%d %H:%M:%S'),
            #     # 已经上机时间
            #     'cost_time': self.cost_time,
            #     # 计费方式 目前默认 5分钱/分钟
            #     'charge_mode': 5,
            #     # 当前用户余额
            #     'balance_account': 10000,
            #     # 设备机器码
            #     'device_code': 'xx-xx-xx-xx-xx-xx',
            # }
            # 如果用户余额不足上机了，则强制下机
            ctime = charge_dict.get('ctime')
            if ctime is None:
                log.error("没有关键信息 ctime: charge_str = {}".format(charge_str))
                continue

            charge_mode = charge_dict.get('charge_mode')
            if charge_mode is None:
                log.error("没有关键信息 charge_mode: charge_str = {}".format(charge_str))
                continue

            balance_account = charge_dict.get('balance_account')
            if balance_account is None:
                log.error("没有关键信息 balance_account: charge_str = {}".format(charge_str))
                continue

            now_timestamp = int(time.time())
            start_time = int(time.mktime(time.strptime(ctime, "%Y-%m-%d %H:%M:%S")))
            cost_time = cal_cost_time(now_timestamp - start_time)
            cost_money = cost_time * int(charge_mode)
            # 如果使用的费用超额半分钟的费用，则强制下机
            if cost_money - balance_account >= 0.75 * int(charge_mode):
                log.info("当前用户余额不足，强制下机: record_key = {} balance_account = {} "
                         "cost_time = {}分钟 cost_money = {} start_time = {} now_time = {}".
                         format(record_key, balance_account, cost_time, cost_money, start_time, now_timestamp))
                # 执行下机流程
                if WindowsService.do_offline_order(record_key):
                    log.info("当前用户余额不足, 强制下机完成: record_key = {}".format(record_key))
                else:
                    log.error("强制下机失败: record_key = {}".format(record_key))
                continue

        except Exception as e:
            log.error("当前存入的计费数据格式不正确: charge_str = {}".format(charge_str))
            log.exception(e)
            continue


# 启动计费线程
def charging_thread():
    log.info("开始启动计费线程...")

    SLEEP_TIME = 60
    while True:
        try:
            start_time = time.time()
            # 找出所有用户
            record_key_list = cache_client.keys(pattern=REDIS_PRE_RECORD_KEY + '*')

            # 给当前线上用户进行计费
            do_charging(record_key_list)

            log.info("扣费操作耗时: {} s".format(time.time() - start_time))

        except Exception as e:
            log.error("计费线程异常:")
            log.exception(e)
        time.sleep(SLEEP_TIME)


def parse_time(string):
    hour, minute, second = string.split(":")
    cron = {
        "minute": minute,
        "hour": hour,
        "day": "*",
        "month": "*",
        "day_of_week": "*",
    }
    return cron


# 更新游戏
def update_game():
    log.info("开始后台更新游戏...")
    if DeviceGameService.update_game_all_by_http():
        log.info("游戏更新成功!")
    else:
        log.error("游戏更新失败!")
    log.info("后台更新游戏完成...")


# 后台更新游戏线程
def update_game_thread():
    log.info("开始启动定时更新游戏线程...")
    pre_update_time = DEFAULT_GAME_UPDATE_TIME
    update_job_id = "update_game"

    parse_time(pre_update_time)

    # 启动定时调度器框架
    scheduler = BackgroundScheduler(logger=log, timezone="Asia/Shanghai")
    scheduler.add_job(update_game, trigger="cron", id=update_job_id, **parse_time(pre_update_time))
    scheduler.start()

    SLEEP_TIME = 30
    while True:

        while True:
            try:
                # 获取当前游戏更新时间
                time_str = DeviceGameService.get_game_update_time(cache_client)
                if time_str == pre_update_time:
                    log.info("当前定时更新游戏时间: {}".format(time_str))
                    break

                log.info("当前游戏更新时间发生变更: pre = {} cur = {}".format(pre_update_time, time_str))
                pre_update_time = time_str
                scheduler.reschedule_job(update_job_id, trigger="cron", **parse_time(time_str))
            except Exception as e:
                log.error("游戏更新调度周期异常:")
                log.exception(e)
            break

        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    # 刷新微信缓存线程
    access_token_handler = threading.Thread(target=access_token_thread)
    access_token_handler.start()

    # 刷新上线扣费线程
    charging_handler = threading.Thread(target=charging_thread)
    charging_handler.start()

    # 定时更新线程
    game_update_handler = threading.Thread(target=update_game_thread)
    game_update_handler.start()

    access_token_handler.join()
    charging_handler.join()
    game_update_handler.join()
