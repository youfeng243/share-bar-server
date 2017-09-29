# -*- coding: utf-8 -*-

import json

import requests
from requests_futures.sessions import FuturesSession

import settings
from exts.common import log, REQUEST_SMS_CODE_URL, VERIFY_SMS_CODE, DEFAULT_MOBILE_EXPIRED
from exts.database import redis
from exts.leancloud import LeanCloud

lean_cloud_client = LeanCloud(settings.LEANCLOUD_ID, settings.LEANCLOUD_KEY)


def sms_default_callback(session, resp):
    log.log.info('requestSms Resp: %s', resp.json())


# 短信验证码服务
def request_sms(mobile):
    if settings.DEBUG:
        log.info("当前处于调试状态，不进行短信验证码验证...")
        return True

    data = {'mobilePhoneNumber': mobile}
    log.info('requestSms: %s', mobile)
    headers = lean_cloud_client.gen_headers(_sign=False)
    log.info('headers: %s', headers)
    if not settings.LEANCLOUD_PUSH_ENABLED:
        log.warn('没有打开短信验证码功能!!!!')
        return False

    session = FuturesSession()
    try:
        session.post(
            REQUEST_SMS_CODE_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=10,
            background_callback=sms_default_callback)
        log.info("发送短信请求成功: mobile = {}".format(mobile))
        return True
    except Exception as e:
        log.error("发送验证码请求失败:")
        log.exception(e)

    return False


# 这里是校验手机验证码
def validate_captcha(mobile, captcha):
    if settings.DEBUG or settings.TESTING:
        if captcha == settings.SMS_DEBUG_CODE:
            return True
        log.info("调试模式验证码校验失败: 发送过来的验证码 = {} 需要校验的调试验证码 = {}".format(
            captcha, settings.SMS_DEBUG_CODE))
        return False

    # 判断是否已经设置了 短信验证码关键信息
    if settings.LEANCLOUD_ID or not settings.LEANCLOUD_KEY:
        raise RuntimeError('没有设定 leancloud id/key')

    url = VERIFY_SMS_CODE.format(captcha=captcha)
    try:
        resp = requests.post(url,
                             params={'mobilePhoneNumber': mobile},
                             headers=lean_cloud_client.gen_headers(_sign=False),
                             )
        data = resp.json()
        rt = data.get('code', None)
        log.info('veriftySms(%s): %s', mobile, data)
        return rt is None
    except Exception as e:
        log.error("请求验证短信验证码失败: phone = {} captcha = {}".format(mobile, captcha))
        log.exception(e)
    return False


# 记录当前手机号码已经发过一次验证码，存入redis 一分钟后过期
def mobile_reach_ratelimit(mobile):
    if settings.DEBUG:
        log.info("调试模式下，可以无限次请求验证码!")
        return False

    key = 'bar:ratelimit:mobile:captcha:%s' % mobile
    value = redis.get(key)
    log.info('redis[%s]: %s', key, value)
    if value is not None:
        return True

    redis.setex(key, DEFAULT_MOBILE_EXPIRED, mobile)
    return False
