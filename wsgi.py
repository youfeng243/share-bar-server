# -*- coding: utf-8 -*-
from flask import request
from werkzeug.contrib.fixers import ProxyFix

from app import create_app
from exts.common import log
from tools.signature import check_signature

log.info("开始进入初始化流程..")
application = create_app('share-bar-server')

application.wsgi_app = ProxyFix(application.wsgi_app)


@application.route('/', methods=['GET'])
@check_signature
def index():
    log.info("微信心跳....")
    return request.args.get('echostr')


@application.route("/test")
def run_status():
    log.info("server is running...")
    return "server is runing..."


if __name__ == "__main__":
    application.run(port=8080)
