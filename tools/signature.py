# -*- coding: utf-8 -*-

import copy
import hashlib
import json
import random
import string
from functools import wraps
from urllib import urlencode
from urlparse import ParseResult

import requests
from flask import g
from flask import has_request_context
from flask import request
from flask import session
from flask import url_for

import settings
from exts.common import HTTP_FORBIDDEN, fail, log, HTTP_BAD_REQUEST


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

        log.info("微信-signature: {}".format(signature))
        log.info("微信-timestamp: {}".format(timestamp))
        log.info("微信-nonce: {}".format(nonce))

        token = settings.WECHAT_TOKEN

        cal_signature = gen_signature(timestamp, nonce, token)
        if not cal_signature == signature:
            log.warn("微信-%s != %s" % (signature, cal_signature))
            return fail(HTTP_FORBIDDEN)

        log.info("微信-签名校验成功: {}".format(cal_signature))
        return func(*args, **kwargs)

    return decorator


# 获得微信鉴权url
def get_oauth_url(endpoint, state):
    args = copy.deepcopy(request.args.to_dict())
    args.update(request.view_args)
    url = url_for(endpoint, _external=True, **args)
    qs = urlencode({
        'appid': settings.WECHAT_APP_ID,
        'redirect_uri': url,
        'scope': 'snsapi_userinfo',
        'state': state,
    })
    try:
        o = ParseResult('https', 'open.weixin.qq.com',
                        '/connect/oauth2/authorize', '',
                        query=qs, fragment='wechat_redirect')
        return o.geturl()
    except Exception as e:
        log.error("解析参数失败:")
        log.exception(e)
    return None


# 获得微信url token
def get_token_url(code):
    args = copy.deepcopy(request.args.to_dict())
    args.update(request.view_args)
    qs = urlencode({
        'appid': settings.WECHAT_APP_ID,
        'secret': settings.WECHAT_APP_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
    })
    try:
        o = ParseResult('https', 'api.weixin.qq.com',
                        '/sns/oauth2/access_token', '',
                        query=qs, fragment='wechat_redirect')
        return o.geturl()
    except Exception as e:
        log.error("解析参数失败:")
        log.exception(e)
    return None


# 微信登录
def user_login_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):

        if not has_request_context():
            return fail(HTTP_BAD_REQUEST, u"服务访问异常!")

        openid = session.get('openid', None)
        if openid is None:
            code = request.args.get('code', None)
            if code is None:
                return fail(HTTP_BAD_REQUEST, u"参数错误: 没有code参数, 无法登录!")

            url = get_token_url(code)
            if url is None:
                return fail(HTTP_BAD_REQUEST, u"获得微信token失败!")

            try:
                resp = requests.get(url, verify=False, timeout=30)
                if resp.status_code == 200:
                    data = json.loads(resp.content)
                    openid = data.get('openid', None)
                    session['openid'] = openid
                    g.openid = openid
                    return func(*args, **kwargs)
            except Exception as e:
                log.error("获取用户openid失败:")
                log.exception(e)
            return fail(HTTP_BAD_REQUEST, u"微信授权失败!")
        # else:
        #     # return fail(HTTP_BAD_REQUEST, u"微信登录异常!")
        #     if request.method == 'GET':
        #         url = get_oauth_url(request.endpoint, random.randint(1, 10))
        #         if url is None:
        #             log.error("获取微信鉴权url失败...")
        #             return fail(HTTP_BAD_REQUEST, u"获取微信鉴权url失败!")
        #         log.info("当前微信鉴权url = {}".format(url))
        #         return redirect(url)
        g.openid = openid
        return func(*args, **kwargs)

    return decorator


# 微信登录
# def user_login_required(*args, **kwargs):
#     if request.endpoint != 'wechat.index':
#         openid = session.get('openid', None)
#         if openid is None and has_request_context():
#             code = request.args.get('code', None)
#             if code is not None:
#                 url = get_token_url(code)
#                 resp = requests.get(url, verify=False)
#                 if resp.status_code == 200:
#                     data = json.loads(resp.content)
#                     openid = data.get('openid', None)
#                     session['openid'] = openid
#             else:
#                 if request.method == 'GET':
#                     url = get_oauth_url(request.endpoint, randint(1, 10))
#                     logger.info(url)
#                     return redirect(url)
#         g.wechat_openid = openid


def signature_mch_info(params):
    args = params.items()
    result = sorted(args, cmp=lambda x, y: cmp(x[0], y[0]))
    result = ['%s=%s' % (key, value) for key, value in result if value != '']
    to_hash = '%s&key=%s' % ('&'.join(result), settings.WECHAT_PAYMENT_SECRET)
    hashed = hashlib.md5(to_hash).hexdigest()
    return hashed.upper()


def get_nonce_str(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))
