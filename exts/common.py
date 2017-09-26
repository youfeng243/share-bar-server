#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: common.py
@time: 2017/8/28 20:58
"""

import json

from flask import Response

from logger import Logger

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500
HTTP_NOT_IMPLEMENTED = 501

'''
登录错误码
'''
# 当前用户没有登录
LOGIN_ERROR_BIND = -1
# 当前用户已经被删除
LOGIN_ERROR_DELETE = -2
# 当前用户被禁止使用
LOGIN_ERROR_FORBID = -3
# 当前设备不存在
LOGIN_ERROR_NOT_FIND = -4
# 用户余额不足
LOGIN_ERROR_NOT_SUFFICIENT_FUNDS = -5
# 上线失败 未知错误
LOGIN_ERROR_UNKNOW = -6

ERROR_MSG = {
    HTTP_OK: 'OK',
    HTTP_BAD_REQUEST: 'bad request',
    HTTP_UNAUTHORIZED: 'unauthorized',
    HTTP_FORBIDDEN: 'forbidden',
    HTTP_NOT_FOUND: 'not found',
    HTTP_SERVER_ERROR: 'server error',
    HTTP_NOT_IMPLEMENTED: 'not implemented',
}

# 短信验证码相关
DEFAULT_MOBILE_EXPIRED = 60  # 1 minute
LEANCLOUD_HOST = 'https://api.leancloud.cn'
REQUEST_SMS_CODE_URL = ''.join([LEANCLOUD_HOST, '/1.1/requestSmsCode'])
VERIFY_SMS_CODE = ''.join([LEANCLOUD_HOST, '/1.1/verifySmsCode/{captcha}'])

log = Logger('share-bar-server.log').get_logger()


def json_resp(data, http_status):
    return Response(data, status=http_status, mimetype="application/json")


# 数据列表返回打包
def package_result(total, page_list):
    return {"total": total, "data": page_list}


# 返回成功
def success(result=u"success", **kwargs):
    resp = {
        'success': True,
        'error': None,
        'result': result
    }
    if kwargs:
        resp.update(kwargs)
    data = json.dumps(resp)
    return json_resp(data, HTTP_OK)


# 返回失败
def fail(http_status, error=None, result=None):
    resp = {
        'success': False,
        'error': error or ERROR_MSG.get(http_status, "undefined error"),
        'result': result
    }
    data = json.dumps(resp)
    return json_resp(data, http_status)
