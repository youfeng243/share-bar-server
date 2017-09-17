# -*- coding: utf-8 -*-

from werkzeug.contrib.fixers import ProxyFix

from app import create_app
from exts.common import log

log.info("开始进入初始化流程..")
application = create_app('share-bar-server')

application.wsgi_app = ProxyFix(application.wsgi_app)


@application.route("/")
@application.route("/home")
@application.route("/index")
def index():
    log.info("server is running...")
    return "server is runing..."


if __name__ == "__main__":
    application.run(port=8888)
