#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/20 14:13
"""
from flask import Blueprint
from flask import request

from exts.common import log
from tools.signature import check_signature

bp = Blueprint('wechat', __name__)


# bp.before_request(wechat_login)


@bp.route('/', methods=['GET'])
@check_signature
def index():
    log.info("微信心跳....")
    return request.args.get('echostr')
