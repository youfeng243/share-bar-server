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
