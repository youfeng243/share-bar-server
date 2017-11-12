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
from exts.common import log
from exts.mongo import MongDb
from exts.redis_api import RedisClient
from exts.sms_api import SmsClient

# mysql 数据库接口
db = SQLAlchemy()

# 微信缓存，上机缓存
redis_cache_client = RedisClient(db=0)

# 设备信息缓存，设备状态 需要放入内存中，实时控制
redis_device_client = RedisClient(db=1)

# 短信接口
sms_client = SmsClient(redis_cache_client, settings.TX_SMS_APP_ID, settings.TX_SMS_APP_KEY,
                       settings.TX_SMS_TEXT_TEMP_ID)

# mongodb
mongodb = MongDb(settings.MONGO_HOST,
                 settings.MONGO_PORT,
                 settings.MONGO_DB,
                 log=log)
