from flask_sqlalchemy import SQLAlchemy

import settings
from exts.redis_api import RedisClient
from exts.sms_api import SmsClient

db = SQLAlchemy()
redis_client = RedisClient()
sms_client = SmsClient(redis_client, settings.TX_SMS_APP_ID, settings.TX_SMS_APP_KEY, settings.TX_SMS_TEXT_TEMP_ID)
