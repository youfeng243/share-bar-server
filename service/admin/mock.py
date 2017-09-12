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
from service.admin.model import Admin


def gen_admin():
    for _ in xrange(30):
        username = 'lzz{}'.format(_)
        password = 'youfeng{}'.format(_)
        name = 'lzzyoufeng{}'.format(_)

        Admin.create(username, password, name, 1)

    log.info("创建管理员数据完成...")
