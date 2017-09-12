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
from service.address.model import Address


def gen_address():

    for _ in xrange(40):
        Address.create("广东省", "深圳市", "宝安区", "宝安汽车站{}".format(_), 0)

    Address.create("广东省", "深圳市", "宝安区", "宝安汽车站", 0)
    Address.create("广东省", "深圳市", "宝安区", "白金时代公寓", 0)
    Address.create("广东省", "深圳市", "南山区", "芒果网大厦", 0)
    Address.create("广东省", "深圳市", "南山区", "A8音乐大厦", 0)
    Address.create("广东省", "深圳市", "南山区", "腾讯大厦", 0)
    Address.create("广东省", "深圳市", "南山区", "1111", 0)
    Address.create("广东省", "深圳市", "南山区", "22222", 0)
    Address.create("广东省", "深圳市", "南山区", "33333", 0)
    Address.create("广东省", "深圳市", "南山区", "44444", 0)
    Address.create("广东省", "深圳市", "南山区", "445454", 0)
    Address.create("广东省", "深圳市", "南山区", "fasdf", 0)
    Address.create("广东省", "深圳市", "南山区", "fdas", 0)
    Address.create("广东省", "深圳市", "南山区", "fasdfdsaff", 0)
    Address.create("广东省", "深圳市", "南山区", "fasdfsafsad", 0)
    Address.create("广东省", "深圳市", "南山区", "fdsafadfs", 0)
    Address.create("广东省", "深圳市", "南山区", "fdsafweewf", 0)
    Address.create("广东省", "深圳市", "南山区", "vcxzvzxcv", 0)
    log.info("创建地址数据完成...")
