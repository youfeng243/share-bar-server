#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: settings.py
@time: 2017/9/4 20:30
"""
DEBUG = False
MOCK = False
SECRET_KEY = "4&^^%%$%BJHGFGHHVVBN%$$#^"
SQLALCHEMY_DATABASE_URI = 'mysql://root:doumihuyuqaz@localhost:3306/share_bar_db?charset=utf8mb4'
# SQLALCHEMY_DATABASE_URI = 'mysql://root:doumihuyuqaz@39.108.60.25:3306/share_bar_db?charset=utf8mb4'
SQLALCHEMY_COMMIT_ON_TEARDOWN = True
SQLALCHEMY_TRACK_MODIFICATIONS = True
REDIS_URI = "redis://localhost:6379"
# redis 最大连接数
REDIS_MAX_CONNECTIONS = 32
WECHAT_APP_ID = "wx9984ca5754273e7d"
WECHAT_TOKEN = "fsfjdsalkf"
WECHAT_PAYMENT_SECRET = "3ea206fd5440e8ffe5025568990bbd79"
WECHAT_APP_SECRET = "9ed565f37130030341086824b2eeca43"
WECHAT_MCH_ID = "1488747842"

# sms 短信开关，是否使用
SMS_ENABLED = True
SMS_DEBUG_CAPTCHA = '123456'

# 未收到心跳最长时间，超过该时间则强制下机
MAX_LOST_HEART_TIME = 300

# 腾讯短信
TX_SMS_APP_ID = 1400045488
TX_SMS_APP_KEY = "9ea6fb2180a0cd7434c9ce69fc8b12be"
TX_SMS_TEXT_TEMP_ID = 49320
