# !/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: gun_config.py
@time: 2017/8/28 20:45
"""

from common import log, app

log.info("开始初始化服务...")


@app.route("/")
def index():
    log.info("server is running...")
    return "server is runing..."


if __name__ == "__main__":
    app.run(port=8888)
