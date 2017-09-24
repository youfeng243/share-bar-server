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
from service.user.impl import UserService


def gen_user():
    for _ in xrange(200):
        num = 100 + _
        phone = '13532369{}'.format(num)

        UserService.create(phone, str(num), str(num))

    log.info("创建用户数据完成...")
