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
from flask_login.utils import _cookie_digest
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
默认费率
'''
DEFAULT_CHARGE_MODE = 5

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
# 当前设备已经在使用上线了，但是不是当前用户在使用!
LOGIN_ERROR_DEVICE_IN_USING = -7
# 当前用户已经在使用上线了，但是不是当前设备在使用
LOGIN_ERROR_USER_IN_USING = -8
# 当前设备不处于空闲状态，不能上机
LOGIN_ERROR_DEVICE_NOT_FREE = -9

'''
redis 缓存公共前缀管理
'''

# 最新费率
REDIS_NEWEST_CHARGE_MODE = 'bar#charge#newest'

# 上线记录关联前缀
REDIS_PRE_RECORD_KEY = 'bar#online#record#'

# 用户上线前缀
REDIS_PRE_USER_KEY = 'bar#online#player#'

# 设备上线前缀
REDIS_PRE_DEVICE_KEY = 'bar#online#device#'

# 上线token前缀
REDIS_PRE_DEVICE_CODE_KEY = 'bar#online#device_code#'

# 上线保持连接key前缀
REDIS_PRE_USER_ONLINE_KEY = 'bar#user#online#'

# 手机号验证码验证码过期时间, 控制手机请求验证码的频率 60s
REDIS_PRE_MOBILE_EX_KEY = 'bar#ratelimit#mobile#'

# 手机验证码保存在redis中的时间
REDIS_PRE_CAPTCHA_EX_KEY = 'bar#ratelimit#captcha#'

# 设备心跳key
REDIS_PRE_DEVICE_HEART_KEY = 'bar#device#heart#'

# 设备状态key
REDIS_PRE_DEVICE_STATUS_KEY = 'bar#device#status#'

# 设备存活状态最后同步时间
REDIS_PRE_DEVICE_ALIVE_SYNC_LAST_TIME_KEY = 'bar#device#alive#sync#lasttime'

# 网页token存储缓存前缀
REDIS_PRE_OPENID_KEY = 'bar#access#openid#'

# 在redis中的key
WECHAT_ACCESS_TOKEN_KEY = "bar#global#access_token"

# 在redis中的key
WECHAT_JSAPI_TICKET_KEY = "bar#global#jsapi_ticket"

'''
前端相对路径URL
'''
# 跳转到关注文章链接
ATTENTION_URL = 'http://mp.weixin.qq.com/s/gyJKttwpg3nq-dEpiNTM8Q'

ERROR_MSG = {
    HTTP_OK: 'OK',
    HTTP_BAD_REQUEST: 'bad request',
    HTTP_UNAUTHORIZED: 'unauthorized',
    HTTP_FORBIDDEN: 'forbidden',
    HTTP_NOT_FOUND: 'not found',
    HTTP_SERVER_ERROR: 'server error',
    HTTP_NOT_IMPLEMENTED: 'not implemented',
}

'''
redis 过期时间管理
'''
# 手机请求验证码时间间隔
DEFAULT_EXPIRED_MOBILE = 60  # 1 minute

# 短信验证码存储时间
DEFAULT_EXPIRED_CAPTCHA = 300  # 5 分钟

# 费率过期时间
DEFAULT_EXPIRED_CHARGE = 3600  # 一个小时过期

# 设备心跳过期时间
DEFAULT_EXPIRED_DEVICE_HEART = 300  # 5 分钟

# 设备存活信息同步周期
DEFAULT_EXPIRED_DEVICE_ALIVE_SYNC = 300  # 5 分钟

# 设备状态缓存时间
DEFAULT_EXPIRED_DEVICE_STATUS = 24 * 3600  # 缓存设备状态 1天

# 日志管理
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


# 获得当前最新时间
def get_now_time():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
