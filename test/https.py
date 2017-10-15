#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: https.py
@time: 2017/10/15 15:49
"""
import requests

r = requests.get('https://datasyncs.sz.haizhi.com:18443', verify=False)
print r.status_code
print r.text