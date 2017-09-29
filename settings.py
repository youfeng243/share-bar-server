#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: settings.py
@time: 2017/9/4 20:30
"""
DEBUG = True
TESTING = True
MOCK = False
SECRET_KEY = "4&^^%%$%BJHGFGHHVVBN%$$#^"
SQLALCHEMY_DATABASE_URI = 'mysql://root:000000@localhost:3306/share_bar_db?charset=utf8'
SQLALCHEMY_COMMIT_ON_TEARDOWN = True
SQLALCHEMY_TRACK_MODIFICATIONS = True
REDIS_URI = "redis://localhost:6379"
WECHAT_APP_ID = "wx9984ca5754273e7d"
WECHAT_TOKEN = "fsfjdsalkf"
WECHAT_PAYMENT_SECRET = "3ea206fd5440e8ffe5025568990bbd79"
WECHAT_APP_SECRET = "9ed565f37130030341086824b2eeca43"
WECHAT_MCH_ID = "1488747842"

# 蓝灯sms
LEANCLOUD_ID = None
LEANCLOUD_KEY = None
# sms 短信开关，是否使用
LEANCLOUD_PUSH_ENABLED = False
SMS_DEBUG_CODE = '123456'
