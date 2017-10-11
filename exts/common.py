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
from flask.ext.login.utils import _cookie_digest
from werkzeug.security import safe_str_cmp

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
# 设备已经在使用了
LOGIN_ERROR_DEVICE_IN_USING = -7
# 当前用户已经在线了
LOGIN_ERROR_USER_IN_USING = -8
# 当前设备不处于空闲状态，不能上机
LOGIN_ERROR_DEVICE_NOT_FREE = -9

'''
redis 缓存公共前缀管理
'''
# 锁key前缀
# REDIS_PRE_LOCK_KEY = 'offline#lock#'

# 上线记录关联前缀
REDIS_PRE_RECORD_KEY = 'online#record#'

# 用户上线前缀
REDIS_PRE_USER_KEY = 'online#player#'

# 设备上线前缀
REDIS_PRE_DEVICE_KEY = 'online#device#'

# 上线token前缀
REDIS_PRE_DEVICE_CODE_KEY = 'online#device_code#'

# 上线保持连接key前缀
REDIS_PRE_KEEP_ALIVE_KEY = 'keepalive#'

# 网页token存储缓存前缀
REDIS_PRE_OPENID_KEY = 'access#openid#'

# 在redis中的key
WECHAT_ACCESS_TOKEN_KEY = "global:access_token"

# 在redis中的key
WECHAT_JSAPI_TICKET_KEY = "global:jsapi_ticket"

'''
前端相对路径URL
'''

ATTENTION_URL = 'https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzUzMzI4NDQzNQ==&scene=124#wechat_redirect'

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
LEANCLOUD_HOST = 'https://leancloud.cn'
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


def encode_user_id(user_id):
    '''
    This will encode a ``unicode`` value into a cookie, and sign that cookie
    with the app's secret key.

    :param user_id: The value to encode, as `unicode`.
    :type user_id: unicode
    '''
    return u'{0}|{1}'.format(str(user_id), _cookie_digest(str(user_id)))


def decode_user_id(cookie):
    '''
    This decodes a cookie given by `encode_cookie`. If verification of the
    cookie fails, ``None`` will be implicitly returned.

    :param cookie: An encoded cookie.
    :type cookie: str
    '''
    try:
        payload, digest = cookie.rsplit(u'|', 1)
        if hasattr(digest, 'decode'):
            digest = digest.decode('ascii')  # pragma: no cover
    except ValueError:
        return None

    if safe_str_cmp(_cookie_digest(payload), digest):
        return payload

    return None


# 时间转换 秒转分
def cal_cost_time(seconds):
    log.info("需要转换的时间: seconds = {}".format(seconds))
    if seconds < 30:
        seconds = 0
    if 30 <= seconds < 60:
        seconds = 60

    minutes = seconds // 60 + (1 if seconds % 60 != 0 else 0)
    log.info("计算后的时间: minutes = {}".format(minutes))
    return minutes
