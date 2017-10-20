#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: resource.py
@time: 2017/8/28 20:58
"""

from flask_sqlalchemy import SQLAlchemy

import settings
from exts.redis_api import RedisClient
from exts.sms_api import SmsClient

# mysql 数据库接口
db = SQLAlchemy()

# 微信缓存，上机缓存
redis_cache_client = RedisClient(db=0)

# 短信接口
sms_client = SmsClient(redis_cache_client, settings.TX_SMS_APP_ID, settings.TX_SMS_APP_KEY,
                       settings.TX_SMS_TEXT_TEMP_ID)
