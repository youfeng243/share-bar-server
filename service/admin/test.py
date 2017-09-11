#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: test.py
@time: 2017/9/11 11:53
"""
import json
import unittest

from flask_testing import TestCase

from app import create_app
from exts.common import log


class AdminTest(TestCase):
    def create_app(self):
        app = create_app()
        return app

    # 初始化工作
    def setUp(self):
        log.info("开始初始化测试: {}".format(__name__))

    # 退出清理工作
    def tearDown(self):
        log.info("测试完成: {}".format(__name__))

    def test_login(self):
        r = self.client.post('/admin/sign_in',
                             data=json.dumps({'username': 'youfeng',
                                              'password': '123456'}),
                             content_type='application/json')
        self.assert200(r)
        self.assertEquals(r.json.get('success'), True)

        r = self.client.post('/admin/sign_in',
                             data=json.dumps({'username': 'youfdeng',
                                              'password': '123456'}),
                             content_type='application/json')
        self.assert200(r)
        self.assertNotEquals(r.json.get('success'), True)
        print r.json.get('success')

    def test_logout(self):
        # self.client.post('/admin/sign_in',
        #                  data=json.dumps({'username': 'youfeng',
        #                                   'password': '123456'}),
        #                  content_type='application/json')

        r = self.client.get('/admin/sign_out')
        self.assert200(r)
        self.assertEquals(r.json.get('success'), True)

if __name__ == '__main__':
    unittest.main()
