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
    phone_list = db.relationship('Phone', backref='user', lazy='dynamic')

    # def __init__(self, account, email):
    #     self.account = account
    #     self.email = email
    @classmethod
    def create(cls, account=10):
        user = User(account=account)
        db.session.add(user)
        db.session.commit()
        return user


class Phone(db.Model):
    __tablename__ = 'phone'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    userId = db.Column(db.Integer, db.ForeignKey('user.id'))
    attr_list = db.relationship('Attr', backref='phone', lazy='dynamic')

    @classmethod
    def create(cls, name, userId):
        phone = Phone(name=name, userId=userId)
        db.session.add(phone)
        db.session.commit()
        return phone

        # def __init__(self, name, factory, userId):
        #     self.name = name
        #     self.factory = factory
        #     self.userId = userId


class Attr(db.Model):
    __tablename__ = 'attr'
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.String(20))
    phoneId = db.Column(db.Integer, db.ForeignKey('phone.id'))

    @classmethod
    def create(cls, price, phoneId):
        attr = Attr(price=price, phoneId=phoneId)
        db.session.add(attr)
        db.session.commit()
        return attr

        # def __init__(self, color, price, phoneId):
        #     self.color = color
        #     self.price = price
        #     self.phoneId = phoneId


db.drop_all()
db.create_all()
print '数据库创建完成..'
user1 = User.create(10)
user2 = User.create(11)
user3 = User.create(12)
user4 = User.create(13)

phone1 = Phone.create('lzz1', user1.id)
phone11 = Phone.create('lzz11', user1.id)
phone2 = Phone.create('lzz2', user2.id)
phone22 = Phone.create('lzz22', user2.id)

phone3 = Phone.create('lzz3', user3.id)
phone33 = Phone.create('lzz33', user3.id)
phone4 = Phone.create('lzz4', user4.id)
phone44 = Phone.create('lzz44', user4.id)

attr1 = Attr.create(11, phone1.id)
attr11 = Attr.create(111, phone11.id)
attr2 = Attr.create(12, phone2.id)
attr12 = Attr.create(121, phone22.id)
attr3 = Attr.create(13, phone3.id)
attr13 = Attr.create(131, phone33.id)
attr4 = Attr.create(14, phone4.id)
attr14 = Attr.create(141, phone44.id)

print user1.phone_list.count()
print [item.name for item in user1.phone_list.paginate(page=1, per_page=1, error_out=False).items]
