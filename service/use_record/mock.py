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
from service.use_record.model import UseRecord


def gen_use_record():
    for _ in xrange(200):
        UseRecord.create(1, 1, "广东省", "深圳市", "南山区", "芒果网大厦")

    log.info("创建使用记录数据完成...")
