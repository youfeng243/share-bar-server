# -*- coding: utf-8 -*-

import copy
import hashlib
import json
import random
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
from exts.common import fail, log, HTTP_OK, decode_user_id, WECHAT_ACCESS_TOKEN_KEY
from exts.redis_api import RedisClient
from exts.resource import redis_cache_client
from service.user.impl import UserService


def gen_signature(timestamp, nonce, token):
    array = [timestamp, nonce, token]
    array = sorted(array)
    sig_str = ''.join(array)
    signature = hashlib.sha1(sig_str).hexdigest()
    return signature


# 生成jsapi签名
def gen_jsapi_signature(timestamp, nonce, jsapi_ticket, url):
    params = {
        'noncestr': nonce,
        'jsapi_ticket': jsapi_ticket,
        'timestamp': str(timestamp),
        'url': url
    }
    result = sorted(params.items(), key=lambda item: item[0])
    result_list = ['{}={}'.format(k, v) for k, v in result]
    to_hash = '&'.join(result_list)
    signature = hashlib.sha1(to_hash).hexdigest()
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
# def get_oauth_url(endpoint, state):
#     args = copy.deepcopy(request.args.to_dict())
#     args.update(request.view_args)
#     url = url_for(endpoint, _external=True, **args)
#     log.info("当前鉴权后回调url为: {}".format(url))
#     qs = urlencode({
#         'appid': settings.WECHAT_APP_ID,
#         'redirect_uri': url,
#         'scope': 'snsapi_userinfo',
#         'state': state,
#     })
#
#     return ParseResult('https', 'open.weixin.qq.com',
#                        '/connect/oauth2/authorize', '',
#                        query=qs, fragment='wechat_redirect').geturl()


# 获得跳转到登录链接的鉴权url
def get_login_oauth_url():
    state = random.randint(1, 10)
    # log.info(request.args)
    # log.info("name = {}".format(auth_url))
    # login_url = url_for("wechat.menu", name=name, _external=True)

    args = copy.deepcopy(request.args.to_dict())
    log.info("当前鉴权 args = {}".format(args))
    args.update(request.view_args)
    log.info("当前鉴权 view_args args = {}".format(args))
    url = url_for(request.endpoint, _external=True, **args)
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
    return ParseResult('https', 'api.weixin.qq.com',
                       '/sns/oauth2/access_token', '',
                       query=qs, fragment='wechat_redirect').geturl()


# 绑定手机号码
def bind_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        user_id_cookie = session.get('u_id')
        if user_id_cookie is None:
            log.warn("当前session中没有u_id 信息，需要登录...")
            return fail(HTTP_OK, u'当前用户没有登录', -1)

        user_id = decode_user_id(user_id_cookie)
        if user_id is None:
            log.warn("当前用户信息被篡改，需要重新登录: user_id_cookie = {}".format(user_id_cookie))
            return fail(HTTP_OK, u'当前用户登录信息被篡改, 不能登录', -1)

        g.user_id = int(user_id)
        log.info("当前访问用户ID为: user_id = {}".format(g.user_id))
        return func(*args, **kwargs)

    return decorator


# 微信登录
def wechat_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):

        # 判断重新刷新token是否已经过期，如果过期则需要重新授权登录
        openid = session.get('openid', None)
        refresh_token = session.get('refresh_token', None)
        # 如果两个关键的token都存在 则正常进入下面的流程
        if openid is not None and refresh_token is not None:
            g.openid = openid
            g.refresh_token = refresh_token
            return func(*args, **kwargs)

        log.info("session 中没有openid 或者 没有 refresh_token")
        code = request.args.get('code', None)
        if code is None:
            log.info("url中没有code参数...")

            # 授权跳转到
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
                log.warn("解析openid失败: data = {}".format(resp.content))
                return fail(HTTP_OK, u"解析openid失败!")
            session['openid'] = openid

            # 保存refresh_token
            refresh_token = data.get('refresh_token', None)
            if refresh_token is None:
                log.warn("解析refresh_token失败: data = {}".format(resp.content))
                return fail(HTTP_OK, u"解析refresh_token失败!")

            session['refresh_token'] = refresh_token
            log.info("用户初次使用得到refresh_token = {}".format(refresh_token))

            # 保存access_token
            access_token = data.get('access_token', None)
            if access_token is not None:
                # session['access_token'] = access_token
                log.info("用户初次使用得到access_token = {}".format(access_token))

            expires_in = data.get("expires_in", None)

            # 存入redis 中
            if access_token is not None and expires_in is not None:
                # 添加到缓存
                redis_cache_client.setex(RedisClient.get_openid_key(openid), expires_in, access_token)

            g.openid = openid
            g.refresh_token = refresh_token
            log.info("通过url链接获得openid成功: openid = {} refresh_token = {}".format(openid, refresh_token))
            return func(*args, **kwargs)
        except Exception as e:
            log.error("获取用户openid失败:")
            log.exception(e)
        return fail(HTTP_OK, u"微信授权失败!")

    return decorator


# def signature_mch_info(params):
#     args = params.items()
#     result = sorted(args, cmp=lambda x, y: cmp(x[0], y[0]))
#     result = ['%s=%s' % (key, value) for key, value in result if value != '']
#     to_hash = '%s&key=%s' % ('&'.join(result), settings.WECHAT_PAYMENT_SECRET)
#     hashed = hashlib.md5(to_hash).hexdigest()
#     return hashed.upper()


# def get_nonce_str(n):
#     return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))
#

# 获得用户头像和昵称信息
# def get_user_wechat_info(refresh_token, openid):
#     head_img_url = ""
#     nick_name = ""
#     if refresh_token is None or openid is None:
#         log.warn("access_token or openid = None, 无法获取头像昵称信息...")
#         return head_img_url, nick_name
#
#     access_token = redis_cache_client.get(RedisClient.get_openid_key(openid))
#     if access_token is None:
#         # 重新刷新access_token
#         refresh_url = 'https://api.weixin.qq.com/sns/oauth2/refresh_token?appid={}&grant_type=refresh_token&refresh_token={}'.format(
#             settings.WECHAT_APP_ID, refresh_token)
#         try:
#             resp = requests.get(refresh_url, verify=False, timeout=30)
#             if resp.status_code != 200:
#                 log.warn("访问刷新微信access_token信息失败: status_code = {} url = {}".format(resp.status_code, refresh_url))
#                 return head_img_url, nick_name
#
#             log.info("当前获取的用户信息为: text = {}".format(resp.text))
#             data = json.loads(resp.content)
#             if data is None:
#                 log.warn("解析微信access_token失败: data = {}".format(data))
#                 return head_img_url, nick_name
#
#             access_token = data.get('access_token', None)
#             expires_in = data.get('expires_in', None)
#             if access_token is None or expires_in is None:
#                 log.warn("解析微信access_token失败: data = {}".format(data))
#                 return head_img_url, nick_name
#
#             # 存入redis
#             redis_cache_client.setex(RedisClient.get_openid_key(openid), expires_in, access_token)
#
#             log.info("重新刷新微信access_token成功: access_token = {} expires_in = {} openid = {}".format(
#                 access_token, expires_in, openid))
#         except Exception as e:
#             log.error("访问刷新微信access_token信息失败: ")
#             log.exception(e)
#             return head_img_url, nick_name
#
#     url = "https://api.weixin.qq.com/sns/userinfo?access_token={}&openid={}&lang=zh_CN". \
#         format(access_token, openid)
#
#     try:
#         resp = requests.get(url, verify=False, timeout=30)
#         if resp.status_code != 200:
#             log.warn("访问用户信息失败: status_code = {} url = {}".format(resp.status_code, url))
#             return head_img_url, nick_name
#
#         data = json.loads(resp.content)
#         if data is None:
#             log.warn("解析用户信息失败: data = {}".format(data))
#             return head_img_url, nick_name
#
#         head_img_url, nick_name = data.get('headimgurl', ''), data.get('nickname', '')
#         head_img_url = head_img_url.strip()
#         nick_name = nick_name.strip()
#         log.info("当前用户获取的昵称与头像信息为: openid = {} nick_name = {} head_img_url = {}".format(
#             openid, nick_name, head_img_url))
#     except Exception as e:
#         log.error("访问微信用户信息失败: ")
#         log.exception(e)
#
#     return head_img_url, nick_name


# 获得用户的关注状态 以及头像和昵称信息
def get_wechat_user_info(openid):
    # 默认设置是未关注状态
    subscribe, nick_name, head_img_url = 0, '', ''

    if openid is None:
        log.error("openid 为None，未知异常！！！")
        return subscribe, nick_name, head_img_url

    access_token = redis_cache_client.get(WECHAT_ACCESS_TOKEN_KEY)
    if access_token is None:
        log.error("access_token 为None，刷新token进程异常！！！")
        return subscribe, nick_name, head_img_url

    url = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token={}&openid={}&lang=zh_CN'.format(
        access_token, openid)
    try:
        resp = requests.get(url, verify=False, timeout=30)
        if resp.status_code != 200:
            log.error("获取用户信息访问状态码不正确: status_code = {} url = {}".format(
                resp.status_code, url))
            return subscribe, nick_name, head_img_url

        json_data = json.loads(resp.text)
        errcode = json_data.get('errcode')
        if errcode is not None:
            log.error("获取用户信息错误码不正常: {}".format(resp.text))
            return subscribe, nick_name, head_img_url

        subscribe = json_data.get('subscribe')
        if subscribe is None:
            log.error("获取用户信息关注状态不正常: {}".format(resp.text))
            return 0, nick_name, head_img_url

        # 如果用户关注了 才去获取昵称和头像信息
        if subscribe == 1:
            # 获得用户昵称 和头像信息
            nick_name = json_data.get('nickname', '')
            head_img_url = json_data.get('headimgurl', '')
            if isinstance(nick_name, basestring):
                nick_name = nick_name.strip()
            else:
                nick_name = ''
            if isinstance(head_img_url, basestring):
                head_img_url = head_img_url.strip()
            else:
                head_img_url = ''
            log.info("当前用户关注了公众号, 能够获取昵称和头像: openid = {} nick_name = {} head_img_url = {}".format(
                openid, nick_name, head_img_url))

    except Exception as e:
        log.error("访问微信用户链接失败: url = {}".format(url))
        log.exception(e)
    return subscribe, nick_name, head_img_url


# 获得当前用户
def get_current_user(user_id):
    if user_id is None:
        return None

    return UserService.get_by_id(user_id)


# 通过openid获取用户信息
def get_current_user_by_openid(openid):
    if openid is None:
        return None

    return UserService.get_by_openid(openid)
