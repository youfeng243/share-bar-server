#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: test.py
@time: 2017/9/11 11:53
"""
import unittest

from exts.common import log


class AdminTest(unittest.TestCase):
    # 初始化工作
    def setUp(self):
        log.info("开始初始化测试: {}".format(__name__))

    # 退出清理工作
    def tearDown(self):
        log.info("测试完成: {}".format(__name__))

    def test_sum(self):
        log.info("测试测试")


if __name__ == '__main__':
    unittest.main()
