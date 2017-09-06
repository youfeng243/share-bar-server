# coding=utf-8
from flask_login import LoginManager

from service.admin.model import Admin

# 管理员的登录管理
admin_login = LoginManager()
admin_login.session_protection = 'strong'


@admin_login.user_loader
def load_user(user_id):
    return Admin.query.get(user_id)


def setup_admin_login(app):
    admin_login.init_app(app)
