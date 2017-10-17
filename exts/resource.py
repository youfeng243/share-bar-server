from flask_sqlalchemy import SQLAlchemy

from exts.redis_api import RedisClient

db = SQLAlchemy()
redis_client = RedisClient()
