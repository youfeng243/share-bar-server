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
from service.role.model import Role


def gen_role():
    for _ in xrange(30):
        name = '超级管理员{}'.format(_)

        Role.create(name)

    log.info("创建角色数据完成...")
