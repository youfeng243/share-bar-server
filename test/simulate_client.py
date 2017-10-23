#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: test_client.py
@time: 2017/10/22 14:30
"""

import sys
import time

import MySQLdb
import requests

sys.path.append("..")

# 海致配置
from logger import Logger

MYSQL_CONFIG = {
    'host': '39.108.60.25',
    'username': 'root',
    'password': 'doumihuyuqaz',
    'db': 'share_bar_db',
}

# mysql 初始化
mysql_db = MySQLdb.connect(MYSQL_CONFIG['host'],
                           MYSQL_CONFIG['username'],
                           MYSQL_CONFIG['password'],
                           MYSQL_CONFIG['db'], charset="utf8mb4")

# 日志管理
log = Logger('simulate_client.log').get_logger()


# 获得所有设备信息
def get_all_device_code():
    device_list = []
    cursor = mysql_db.cursor()
    sql = "SELECT * FROM device"
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        # 遍历sites
        for row in rows:
            device_code = row[3]
            device_list.append(device_code)
            log.info("加载设备编码: {}".format(device_code))

    except Exception as e:
        log.error("Error: unable to fecth data")
        log.exception(e)
    cursor.close()
    return device_list


def main():
    url = 'http://weixin.doumihuyu.com/windows/check'
    while True:
        device_list = get_all_device_code()

        for device_code in device_list:
            try:
                r = requests.post(url, json={'device_code': device_code})
                log.info("当前请求状态: device_code = {} status_code = {}".format(
                    device_code, r.status_code))
                log.info("请求内容: text = {}".format(r.text))
            except Exception as e:
                log.error("发送请求失败: device_code = {}".format(device_code))
                log.exception(e)

        log.info("发送完成，休眠10s")
        time.sleep(10)


if __name__ == '__main__':
    main()
