# -*- coding: utf-8 -*-

import json

import exts.tx_sms.sms as sender
import settings
from exts.common import log, DEFAULT_MOBILE_EXPIRED, DEFAULT_CAPTCHA_EXPIRED
from exts.redis_api import RedisClient
from exts.tx_sms.tools import SmsSenderUtil


# 发送短信对象封装
class SmsClient(object):
    def __init__(self, redis_client, sms_app_id, sms_app_key, sms_text_temp_id):
        self.__redis = redis_client
        self.tx_sms_sender = sender.SmsSingleSender(sms_app_id, sms_app_key)
        self.sms_text_temp_id = sms_text_temp_id

    # 短信验证码服务
    def request_sms(self, mobile):
        if not settings.SMS_ENABLED:
            log.info("当前处于调试状态，没有打开短信验证码功能, 不发送短信验证码请求...")
            return True

        captcha = str(SmsSenderUtil.get_random())
        resp = self.tx_sms_sender.send_with_param("86", mobile, self.sms_text_temp_id, [captcha], "", "", "")

        try:
            result = json.loads(resp)
            if result.get('result') != 0:
                log.error("发送验证码失败: mobile = {} captcha = {}".format(mobile, captcha))
                log.error("返回错误为: resp = {}".format(resp))
                return False

            # 存储验证码到redis中 只保留五分钟有效
            key = RedisClient.get_captcha_redis_key(mobile)
            self.__redis.setex(key, DEFAULT_CAPTCHA_EXPIRED, captcha)

            log.info("验证码发送成功: mobile = {} captcha = {}".format(mobile, captcha))
            return True
        except Exception as e:
            log.error("发送验证码失败: mobile = {} captcha = {}".format(mobile, captcha))
            log.exception(e)

        return False

    # 这里是校验手机验证码
    def validate_captcha(self, mobile, captcha):
        if not settings.SMS_ENABLED:
            if captcha == settings.SMS_DEBUG_CAPTCHA:
                return True
            log.info("调试模式验证码校验失败: 发送过来的验证码 = {} 需要校验的调试验证码 = {}".format(
                captcha, settings.SMS_DEBUG_CAPTCHA))
            return False

        key = RedisClient.get_captcha_redis_key(mobile)
        value = self.__redis.get(key)
        if value is None:
            log.info("当前手机不存在验证码: {}".format(mobile))
            return False

        if captcha != value:
            log.info("当前手机验证码错误: phone = {} captcha = {} cache = {}".format(
                mobile, captcha, value))
            return False

        # 删除已经验证码完成的验证码
        self.__redis.delete(key)
        log.info("删除手机验证码redis key = {}".format(key))
        return True

    # 记录当前手机号码已经发过一次验证码，存入redis 一分钟后过期
    def mobile_reach_rate_limit(self, mobile):
        if not settings.SMS_ENABLED:
            log.info("调试模式下，可以无限次请求验证码!")
            return False

        key = RedisClient.get_mobile_redis_key(mobile)
        value = self.__redis.get(key)
        log.info('redis[%s]: %s', key, value)
        if value is not None:
            return True

        self.__redis.setex(key, DEFAULT_MOBILE_EXPIRED, mobile)
        return False
