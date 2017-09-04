# -*- coding: utf-8 -*-

from werkzeug.contrib.fixers import ProxyFix

from app import create_app

application = create_app('share-bar-server')

application.wsgi_app = ProxyFix(application.wsgi_app)
