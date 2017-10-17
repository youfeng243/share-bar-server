from flask_sqlalchemy import SQLAlchemy

from exts.redis_dao import Redis

db = SQLAlchemy()
redis = Redis()
