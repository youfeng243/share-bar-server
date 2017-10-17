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
import json
import sys

import requests

sys.path.append("..")
sys.path.append("../..")
from exts.common import log


def update_charge():
    session = requests.Session()
    r = session.post('http://weixin.doumihuyu.com/admin/sign_in', json={
        'username': 'youfeng',
        'password': '123456'
    })
    print r.status_code
    print json.loads(r.text, encoding='utf-8')['error']
    print json.loads(r.text, encoding='utf-8')['result']

    r = session.get('http://weixin.doumihuyu.com/admin/charge/newest')
    print r.status_code
    print json.loads(r.text)['error']
    print json.dumps(json.loads(r.text)['result'], ensure_ascii=False)

    log.info("更新费率完成...")


if __name__ == '__main__':
    update_charge()
