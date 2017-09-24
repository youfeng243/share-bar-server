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
from flask_login import login_required

from service.recharge.model import Recharge

bp = Blueprint('recharge', __name__, url_prefix='/admin')


# 充值接口
@bp.route("/recharge/list", methods=['POST'])
@login_required
def get_recharge_list():
    '''
    page: 当前页码
    size: 每页读取数目, 最大不超过50项
    start_time: 查询的起始时间段 时间段其实时间必须小于或者等于end_time
    end_time: 查询的结束时间段 时间段必须大于或者等于start_time
    :return:
    '''
    # {
    #     "page": 1,
    #
    #     "size": 10,
    #     "user_id": 100
    # }
    return Recharge.search_list()
