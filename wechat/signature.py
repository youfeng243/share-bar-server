# -*- coding: utf-8 -*-

import hashlib
import random
import string
from functools import wraps

from flask import request

import settings
from exts.common import HTTP_FORBIDDEN, fail, log


# 生成签名
def gen_signature(timestamp, nonce, token):
    array = [timestamp, nonce, token]
    array = sorted(array)
    sig_str = ''.join(array)
    signature = hashlib.sha1(sig_str).hexdigest()
    return signature


# 微信心跳校验
def check_signature(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')

        token = settings.WECHAT_TOKEN

        cal_signature = gen_signature(timestamp, nonce, token)
        if not cal_signature == signature:
            log.warn("%s != %s" % (signature, cal_signature))
            return fail(HTTP_FORBIDDEN)

        return func(*args, **kwargs)

    return decorator


def signature_mch_info(params):
    args = params.items()
    result = sorted(args, cmp=lambda x, y: cmp(x[0], y[0]))
    result = ['%s=%s' % (key, value) for key, value in result if value != '']
    to_hash = '%s&key=%s' % ('&'.join(result), settings.WECHAT_PAYMENT_SECRET)
    hashed = hashlib.md5(to_hash).hexdigest()
    return hashed.upper()


def get_nonce_str(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))
