#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: xml_data.py
@time: 2017/9/23 22:39
"""
from lxml import etree


# xml 解析类
class XMLData(object):
    def __init__(self, data):
        self.data = data

    @classmethod
    def parse(cls, data):
        parsed_data = etree.fromstring(data)
        return cls(parsed_data)

    def __getattr__(self, name):
        value = self.data.find(name)
        if value is not None:
            return value.text
        return None
