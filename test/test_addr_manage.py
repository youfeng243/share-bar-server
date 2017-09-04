#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: test_addr_manage.py
@time: 2017/8/30 20:22
"""

from common import db
from model.addr_manage import AddrManage

db.drop_all()
db.create_all()

addr1 = AddrManage("白金时代公寓", 0)
db.session.add(addr1)
addr2 = AddrManage("宝安汽车站", 0)
db.session.add(addr2)
db.session.commit()

addr3 = AddrManage("宝安汽车站11", 0)

print addr1.id
print addr2.id
print addr3.id


db.session.add(addr3)
db.session.commit()
print addr1.id
print addr2.id
print addr3.id

addr = AddrManage.query.filter_by(id=1).first()

print addr.update_time
print addr.effective_date
print addr.address

addr.device_num += 10
db.session.commit()


db.session.delete(addr)
db.session.commit()
print " 删除后的ID = {} ".format(addr.id)

addr_test = AddrManage.query.filter_by(id=10).first()
print addr_test
