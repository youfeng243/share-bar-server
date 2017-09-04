#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: common.py
@time: 2017/8/28 20:58
"""
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.contrib.fixers import ProxyFix

from config import MYSQL_URL
from logger import Logger

# flask 句柄
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# 初始化mysql句柄
app.config['SECRET_KEY'] = 'hard to guess..'
app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URL
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


# 获得当前进程log
def get_pid_log_name(log_name):
    return log_name + '-' + str(os.getpid()) + '.log'


global_logger = Logger(get_pid_log_name('share-bar-server'))
log = global_logger.get_logger()


# 获得当前返回信息
def get_response(code, msg, data=''):
    return {'code': code, 'msg': msg, 'data': data}
