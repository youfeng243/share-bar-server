#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: sig_test.py
@time: 2017/9/25 17:29
"""

# 生成jsapi签名
import hashlib

noncestr1 = 'Wm3WZYTPz0wzccnW'
jsapi_ticket1 = 'sM4AOVdWfPE4DxkXGEs8VMCPGGVi4C3VM0P37wVUCFvkVAy_90u5h9nbSlYy3-Sl-HhTdfl2fzFy1AOcHKP7qg'
timestamp1 = '1414587457'
url1 = 'http://mp.weixin.qq.com?params=value'


def gen_jsapi_signature(timestamp, nonce, jsapi_ticket, url):
    params = {
        'noncestr': nonce,
        'jsapi_ticket': jsapi_ticket,
        'timestamp': str(timestamp),
        'url': url
    }
    result = sorted(params.items(), key=lambda item: item[0])
    print result
    result_list = ['{}={}'.format(k, v) for k, v in result]
    to_hash = '&'.join(result_list)
    signature = hashlib.sha1(to_hash).hexdigest()
    return signature


if __name__ == '__main__':
    value = gen_jsapi_signature(timestamp1, noncestr1, jsapi_ticket1, url1)
    print value
