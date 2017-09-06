# -*- coding: utf-8 -*-
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer

from app import create_app
from exts.common import log

application = create_app('share-bar-server')


@application.route("/")
@application.route("/home")
@application.route("/index")
def index():
    log.info("server is running...")
    return "server is runing..."


http_server = HTTPServer(WSGIContainer(application))
http_server.listen(8888)
log.info("tornado服务启动...")
IOLoop.instance().start()
