#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: gun.config.py
@time: 2017/8/28 20:45
"""

import multiprocessing

# 监听本机的8081端口
bind = '0.0.0.0:8081'

# preload_app = True

# 开启进程
workers = multiprocessing.cpu_count() * 2 + 1

# 每个进程的开启线程
threads = multiprocessing.cpu_count() * 2

backlog = 2048

# 工作模式为meinheld
worker_class = "egg:meinheld#gunicorn_worker"

# 如果不使用supervisord之类的进程管理工具可以是进程成为守护进程，否则会出问题
daemon = True

# 进程名称
proc_name = 'file_server.proc'

# # 进程pid记录文件
# pidfile = 'log/share-bar-server.pid'

loglevel = 'info'
accesslog = 'log/access.log'
errorlog = 'log/gunicorn.log'

# 接受最大请求数然后重启进程
max_requests = 1000000
max_requests_jitter = 500000
timeout = 1200000
# 最大支持10M
limit_request_line = 0
limit_request_field_size = 0
x_forwarded_for_header = 'X-FORWARDED-FOR'
