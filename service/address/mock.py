#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: mock.py
@time: 2017/9/11 21:18
"""

# 生成数据
from exts.common import log
from exts.database import db
from service.address.model import Address


def gen_address():
    try:
        Address.create("广东省", "深圳市", "宝安区", "宝安汽车站", 0)
        Address.create("广东省", "深圳市", "宝安区", "白金时代公寓", 0)
        Address.create("广东省", "深圳市", "南山区", "芒果网大厦", 0)
        Address.create("广东省", "深圳市", "南山区", "A8音乐大厦", 0)
        Address.create("广东省", "深圳市", "南山区", "腾讯大厦", 0)
        log.info("创建地址数据完成...")
    except:
        db.session.rollback()
        log.info("创建地址数据失败,回滚...")
