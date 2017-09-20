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
SECRET_KEY = '%$%&^%$%&^&^**(*&&^%%$^$'
SQLALCHEMY_DATABASE_URI = 'mysql://root:000000@localhost:3306/share_bar_db?charset=utf8'
SQLALCHEMY_COMMIT_ON_TEARDOWN = True
SQLALCHEMY_TRACK_MODIFICATIONS = True
WECHAT_APP_ID = "wx9984ca5754273e7d"
WECHAT_TOKEN = ""
WECHAT_PAYMENT_SECRET = ""
WECHAT_APP_SECRET = "9ed565f37130030341086824b2eeca43"
WECHAT_MCH_ID = ""
