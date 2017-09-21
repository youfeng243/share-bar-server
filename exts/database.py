from flask_sqlalchemy import SQLAlchemy

from exts.redis import Redis

db = SQLAlchemy()
redis = Redis()
