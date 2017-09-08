#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: db_test.py
@time: 2017/9/8 12:04
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:555556@localhost:3306/test_db?charset=utf8"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


# 建立user表
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    # phone = db.relationship('Phone', backref='user', lazy='dynamic')

    # def __init__(self, account, email):
    #     self.account = account
    #     self.email = email


class Phone(db.Model):
    __tablename__ = 'phone'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    factory = db.Column(db.String(20))
    userId = db.Column(db.Integer, db.ForeignKey('user.id'))
    # attr = db.relationship('Attr', backref='phone', lazy='dynamic')

    # def __init__(self, name, factory, userId):
    #     self.name = name
    #     self.factory = factory
    #     self.userId = userId


class Attr(db.Model):
    __tablename__ = 'attr'
    id = db.Column(db.Integer, primary_key=True)
    color = db.Column(db.String(20))
    price = db.Column(db.String(20))
    phoneId = db.Column(db.Integer, db.ForeignKey('phone.id'))

    # def __init__(self, color, price, phoneId):
    #     self.color = color
    #     self.price = price
    #     self.phoneId = phoneId


db.drop_all()
db.create_all()
print '数据库创建完成..'
