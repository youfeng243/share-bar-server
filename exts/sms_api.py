# -*- coding: utf-8 -*-

import json

import exts.tx_sms.sms as sender
import settings
from exts.common import log, DEFAULT_MOBILE_EXPIRED, DEFAULT_CAPTCHA_EXPIRED
from exts.database import redis
from exts.redis_dao import get_mobile_redis_key, get_captcha_redis_key
from exts.tx_sms.tools import SmsSenderUtil

tx_sms_sender = sender.SmsSingleSender(settings.TX_SMS_APP_ID, settings.TX_SMS_APP_KEY)


# 短信验证码服务
def request_sms(mobile):
    if not settings.SMS_ENABLED:
        log.info("当前处于调试状态，没有打开短信验证码功能, 不发送短信验证码请求...")
        return True

    captcha = str(SmsSenderUtil.get_random())
    resp = tx_sms_sender.send_with_param("86", mobile, settings.TX_SMS_TEXT_TEMP_ID, [captcha], "", "", "")

    try:
        result = json.loads(resp)
        if result.get('result') != 0:
            log.error("发送验证码失败: mobile = {} captcha = {}".format(mobile, captcha))
            log.error("返回错误为: resp = {}".format(resp))
            return False

        # 存储验证码到redis中 只保留五分钟有效
        key = get_captcha_redis_key(mobile)
        redis.setex(key, DEFAULT_CAPTCHA_EXPIRED, captcha)

        log.info("验证码发送成功: mobile = {} captcha = {}".format(mobile, captcha))
        return True
    except Exception as e:
        log.error("发送验证码失败: mobile = {} captcha = {}".format(mobile, captcha))
        log.exception(e)

    return False


# 这里是校验手机验证码
def validate_captcha(mobile, captcha):
    if not settings.SMS_ENABLED:
        if captcha == settings.SMS_DEBUG_CAPTCHA:
            return True
        log.info("调试模式验证码校验失败: 发送过来的验证码 = {} 需要校验的调试验证码 = {}".format(
            captcha, settings.SMS_DEBUG_CAPTCHA))
        return False

    key = get_captcha_redis_key(mobile)
    value = redis.get(key)
    if value is None:
        log.info("当前手机不存在验证码: {}".format(mobile))
        return False

    if captcha != value:
        log.info("当前手机验证码错误: phone = {} captcha = {} cache = {}".format(
            mobile, captcha, value))
        return False

    # 删除已经验证码完成的验证码
    redis.delete(key)
    log.info("删除手机验证码redis key = {}".format(key))
    return True


# 记录当前手机号码已经发过一次验证码，存入redis 一分钟后过期
def mobile_reach_ratelimit(mobile):
    if not settings.SMS_ENABLED:
        log.info("调试模式下，可以无限次请求验证码!")
        return False

    key = get_mobile_redis_key(mobile)
    value = redis.get(key)
    log.info('redis[%s]: %s', key, value)
    if value is not None:
        return True

    redis.setex(key, DEFAULT_MOBILE_EXPIRED, mobile)
    return False
