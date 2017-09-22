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
from flask import redirect
from flask import request
from flask import session
from flask import url_for

import settings
from exts.common import fail, log, HTTP_OK
from exts.database import redis


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
            return fail(HTTP_OK, u"签名不一致")

        log.info("微信-签名校验成功: {}".format(cal_signature))
        return func(*args, **kwargs)

    return decorator


# 获得微信鉴权url
def get_oauth_url(endpoint, state):
    args = copy.deepcopy(request.args.to_dict())
    args.update(request.view_args)
    url = url_for(endpoint, _external=True, **args)
    log.info("当前鉴权后回调url为: {}".format(url))
    qs = urlencode({
        'appid': settings.WECHAT_APP_ID,
        'redirect_uri': url,
        'scope': 'snsapi_userinfo',
        'state': state,
    })

    return ParseResult('https', 'open.weixin.qq.com',
                       '/connect/oauth2/authorize', '',
                       query=qs, fragment='wechat_redirect').geturl()


# 获得跳转到登录链接的鉴权url
def get_login_oauth_url():
    state = random.randint(1, 10)
    login_url = url_for("wechat.menu", name="login", _external=True)

    log.info("当前鉴权后回调url为: {}".format(login_url))
    qs = urlencode({
        'appid': settings.WECHAT_APP_ID,
        'redirect_uri': login_url,
        'scope': 'snsapi_userinfo',
        'state': state,
    })

    return ParseResult('https', 'open.weixin.qq.com',
                       '/connect/oauth2/authorize', '',
                       query=qs, fragment='wechat_redirect').geturl()


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


# 获取刷新token
def get_refresh_token(openid):
    'box:wechat:open:access-token'

    key = 'bar:wechat:refresh:token:{}'.format(openid)
    refresh_token = redis.get(key)
    if refresh_token is not None:
        return refresh_token

    return None


# 微信登录
def wechat_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):

        # 判断重新刷新token是否已经过期，如果过期则需要重新授权登录
        openid = session.get('openid', None)
        if openid is None:
            log.info("session 中没有openid...")
            code = request.args.get('code', None)
            if code is None:
                log.info("url中没有code参数...")

                # 授权跳转到登录界面
                url = get_login_oauth_url()
                if url is not None:
                    return redirect(url)

                log.info("当前不是get请求访问到这里: {}".format(request.method))
                return fail(HTTP_OK, u"微信未授权，请用微信端进行访问!")

            url = get_token_url(code)
            if url is None:
                log.info("获得token链接失败: code = {}".format(code))
                return fail(HTTP_OK, u"获得微信token失败!")

            try:
                log.info("开始获取openid, 获得token链接为: url = {}".format(url))
                resp = requests.get(url, verify=False, timeout=30)
                if resp.status_code != 200:
                    log.warn("访问token链接失败: status_code = {} url = {}".format(resp.status_code, url))
                    return fail(HTTP_OK, u"获取access_token失败!")

                data = json.loads(resp.content)
                if data is None:
                    log.warn("解析access_token失败: data = {}".format(data))
                    return fail(HTTP_OK, u"解析access_token失败!")

                openid = data.get('openid', None)
                if openid is None:
                    log.warn("解析openid失败: data = {}".format(data))
                    return fail(HTTP_OK, u"解析openid失败!")
                session['openid'] = openid

                # 保存refresh_token
                refresh_token = data.get('refresh_token', None)
                if refresh_token is not None:
                    session['refresh_token'] = refresh_token

                # 保存access_token
                access_token = data.get('access_token', None)
                if access_token is not None:
                    session['access_token'] = access_token

                g.openid = openid
                log.info("获得openid成功: {}".format(openid))
                return func(*args, **kwargs)
            except Exception as e:
                log.error("获取用户openid失败:")
                log.exception(e)
            return fail(HTTP_OK, u"微信授权失败!")
        log.info("从session中获取openid成功: openid = {}".format(openid))
        g.openid = openid
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


# 获得用户头像和昵称信息
def get_user_wechat_info(access_token, openid):
    url = "https://api.weixin.qq.com/sns/userinfo?access_token={}&openid={}&lang=zh_CN". \
        format(access_token, openid)
    head_img_url = ""
    nick_name = ""
    try:
        resp = requests.get(url, verify=False, timeout=30)
        if resp.status_code != 200:
            log.warn("访问用户信息失败: status_code = {} url = {}".format(resp.status_code, url))
            return head_img_url, nick_name

        data = json.loads(resp.content)
        if data is None:
            log.warn("解析用户信息失败: data = {}".format(data))
            return head_img_url, nick_name

        head_img_url, nick_name = data.get('headimgurl', ''), data.get('nickname', '')
    except Exception as e:
        log.error("访问微信用户信息失败: ")
        log.exception(e)

    return head_img_url, nick_name