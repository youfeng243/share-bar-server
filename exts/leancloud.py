# -*- coding: utf-8 -*-

from __future__ import absolute_import

import hashlib
import time


# 短信验证码服务
class LeanCloud(object):
    def __init__(self, lc_id, lc_key):
        self.lc_id = lc_id
        self.lc_key = lc_key

    def sign(self, ts):
        text = '%s%s' % (ts, self.lc_key)
        sign = hashlib.md5(text).hexdigest()
        return sign

    def gen_headers(self, _sign=True):
        headers = {
            'X-LC-Id': self.lc_id,
            'Content-Type': 'application/json'
        }
        if _sign is True:
            mill_ts = str(time.time() * 1000)
            sign = self.sign(mill_ts)
            headers['X-LC-Sign'] = '%s,%s' % (sign, mill_ts)
        else:
            headers['X-LC-Key'] = self.lc_key
        return headers
