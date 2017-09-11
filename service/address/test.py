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

import requests

from exts.common import log


def Sum(a, b):
    return a + b


class bddressTest(unittest.TestCase):
    # 初始化工作
    def setUp(self):
        log.info("开始初始化测试...")
        self.session = requests.session()

    # 退出清理工作
    def tearDown(self):
        log.info("测试完成...")

    def testSum(self):
        self.assertEqual(Sum(1, 1), 2, 'test sum fail')


class AddressTest(unittest.TestCase):
    # 初始化工作
    def setUp(self):
        log.info("开始初始化测试...")
        self.session = requests.session()

    # 退出清理工作
    def tearDown(self):
        log.info("测试完成...")

    def testSum(self):
        self.assertEqual(Sum(1, 1), 2, 'test sum fail')


if __name__ == '__main__':
    unittest.main()
