#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: class_test.py
@time: 2017/9/7 17:30
"""
from exts.database import db


class A(db.Model):
    # __tablename__ = 'test'
    __abstract__ = True

    # ID
    # id = db.Column(db.Integer, primary_key=True)

    a = 1
    b = 2
    c = '111'


class B(A):
    __tablename__ = 'testB'
    id = db.Column(db.Integer, primary_key=True)

    @classmethod
    def create(cls, a, b, c):
        aaa = cls(a=a, b=b, c=c)
        return aaa

#
# print A.__dict__
#
# print A().a
# print A().b
# print A().c

# aaa = A.create('11', '22', '33')
# print aaa.a
# print aaa.b
# print aaa.c
# print aaa.id

bbb = B.create('11', '22', '33')
print bbb.a
print bbb.b
print bbb.c
print bbb.id