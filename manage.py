# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask_script import Manager
from setuptools import find_packages

from app import create_app
from exts.database import db

application = create_app('box')
manager = Manager(application)


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
    with application.test_request_context():
        _import_models()

        db.create_all()
        db.session.commit()

        # # 管理员
        # if Admin.query.filter_by(username='youfeng').first() is None:
        #     admin = Admin.create('youfeng', '555556')
        #     admin.save()
        #     logger.info("添加管理员完成...")
        #
        # # 产品
        # if Product.query.filter_by(name='定制防潮防水纸箱').first() is None:
        #     product = Product(name='定制防潮防水纸箱', price=1,
        #                       description='413mmx320mmx257mm', avatar_url='www.baidu.com')
        #     product.save()
        #     logger.info("添加产品完成...")
        #
        # # 存储费用
        # if Mode.query.filter_by(name='普通').first() is None:
        #     mode = Mode(name='普通', price=1, description='普通')
        #     mode.save()
        #     logger.info("添加费用完成...")

        print 'Database Created'


@manager.command
def dropdb():
    with application.test_request_context():
        _import_models()
        db.drop_all()
        db.session.commit()
        print 'Database Dropped'


if __name__ == '__main__':
    manager.run()
