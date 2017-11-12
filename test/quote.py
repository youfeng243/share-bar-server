#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: quote.py
@time: 2017/11/12 22:57
"""


class A(object):
    @staticmethod
    def hello():
        print 'hello'
        B.world()

class B(object):
    @staticmethod
    def world():
        print 'world'

