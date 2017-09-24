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
from datetime import datetime

from exts.common import log
from service.recharge.model import Recharge


def gen_recharge():
    for _ in xrange(200):
        Recharge.create(1, _, _, datetime.now())

    log.info("创建充值数据完成...")
