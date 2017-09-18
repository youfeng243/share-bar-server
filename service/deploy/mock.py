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
import hashlib
import json
import sys

import requests

from app import create_app

sys.path.append("..")
sys.path.append("../..")
from exts.common import log


def gen_deploy():
    session = requests.Session()
    r = session.post('http://127.0.0.1:8080/admin/sign_in', json={
        'username': 'youfeng',
        'password': '123456'
    })
    print r.status_code
    print json.loads(r.text, encoding='utf-8')['error']
    print json.loads(r.text, encoding='utf-8')['result']
    for address_iter in xrange(10):
        province = '广东省'
        city = '深圳市'
        area = '南山区'
        location = '芒果网大厦{}'.format(address_iter)
        for device_iter in xrange(20):
            m2 = hashlib.md5()
            m2.update(str(address_iter * 100 + device_iter))
            device_code = m2.hexdigest()

            json_data = {
                'province': province,
                'city': city,
                'area': area,
                'location': location,
                'device_code': device_code
            }
            r = session.post('http://127.0.0.1:8080/admin/deploy', json=json_data)
            print r.status_code
            print json.loads(r.text)['error']
            print json.dumps(json.loads(r.text)['result'], ensure_ascii=False)

    log.info("创建部署记录数据完成...")


def gen_deploy_test(application):
    client = application.test_client()
    r = client.post('/admin/sign_in', data=json.dumps({
        'username': 'youfeng',
        'password': '123456'
    }), content_type='application/json')
    print r.status_code

    # session = requests.Session()
    # r = session.post('http://127.0.0.1:8080/admin/sign_in', json={
    #     'username': 'youfeng',
    #     'password': '123456'
    # })
    # print r.status_code
    # print json.loads(r.text, encoding='utf-8')['error']
    # print json.loads(r.text, encoding='utf-8')['result']
    for address_iter in xrange(10):
        province = '广东省'
        city = '深圳市'
        area = '南山区'
        location = '芒果网大厦{}'.format(address_iter)
        for device_iter in xrange(20):
            m2 = hashlib.md5()
            m2.update(str(address_iter * 100 + device_iter))
            device_code = m2.hexdigest()

            json_data = {
                'province': province,
                'city': city,
                'area': area,
                'location': location,
                'device_code': device_code
            }
            # r = session.post('http://127.0.0.1:8080/admin/deploy', json=json_data)
            r = client.post('/admin/deploy', data=json.dumps(json_data), content_type='application/json')
            print r.status_code
            # print json.loads(r.text)['error']
            # print json.dumps(json.loads(r.text)['result'], ensure_ascii=False)

    log.info("创建部署记录数据完成...")


if __name__ == '__main__':
    application = create_app('share-bar-server')
    gen_deploy_test(application)
