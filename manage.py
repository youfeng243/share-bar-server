# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask_script import Manager
from setuptools import find_packages

import settings
from app import create_app
from exts.database import db
from service.address.mock import gen_address
from service.admin.mock import gen_admin
from service.admin.model import Admin
from service.deploy.mock import gen_deploy_test
from service.recharge.mock import gen_recharge
from service.role.mock import gen_role
from service.role.model import Role
from service.use_record.mock import gen_use_record
from service.user.mock import gen_user

application = create_app('share-bar-server')
manager = Manager(application)

SUPER_USER = "youfeng"
SUPER_PASS = "123456"
SUPER_NAME = "游丰"


def _import_models():
    puff_packages = find_packages('./service')
    for each in puff_packages:
        guess_module_name = 'service.%s.model' % each
        try:
            __import__(guess_module_name, globals(), locals())
            print 'Find model:', guess_module_name
        except ImportError:
            pass


@manager.command
def syncdb():
    # with application.test_request_context():
    _import_models()

    db.create_all()
    db.session.commit()

    # 判断角色是否存在，不存在则创建
    if Role.get_by_name(Role.SUPER_ADMIN) is None:
        Role.create(Role.SUPER_ADMIN)
        print "超级管理员权限创建完成..."

    if Admin.get_by_username(SUPER_USER) is None:
        Admin.create(SUPER_USER, SUPER_PASS, SUPER_NAME, Role.get_by_name(Role.SUPER_ADMIN).id)
        print "超级管理员角色创建完成..."

    if settings.DEBUG:
        print '当前为测试状态，需要生成测试数据...'
        # 创建地址数据
        gen_address()

        # 创建管理员数据
        gen_admin()

        # 创建部署数据
        gen_deploy_test(application)

        # 生成角色数据
        gen_role()

        # 创建用户数据
        gen_user()

        # 创建用户使用记录
        gen_use_record()

        # 生成充值数据
        gen_recharge()

        print '数据库创建完成...'


@manager.command
def dropdb():
    with application.test_request_context():
        _import_models()
        db.drop_all()
        db.session.commit()
        print '数据库删除完成...'


if __name__ == '__main__':
    manager.run()
