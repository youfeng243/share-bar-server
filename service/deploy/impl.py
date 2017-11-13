#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/11/13 08:49
"""
from exts.common import log, package_result
from service.deploy.model import Deploy


class DeployService(object):
    # 获得对应设备的部署信息
    @staticmethod
    def get_device_deploy_list(device_id, page, size):
        # 获取数据总数目
        total = 0
        result_list = list()

        # 根据设备ID过滤
        query = Deploy.query.filter(Deploy.device_id == device_id)

        # 获取部署信息列表
        item_paginate = query.paginate(page=page, per_page=size, error_out=False)
        if item_paginate is None:
            log.warn("获取部署信息翻页查询失败: device_id = {} page = {} size = {}".format(device_id, page, size))
            return package_result(total, result_list)

        item_list = item_paginate.items
        if item_list is None:
            log.warn("部署信息分页查询失败: device_id = {} page = {} size = {}".format(device_id, page, size))
            return package_result(total, result_list)

        return package_result(item_paginate.total, [item.to_dict() for item in item_list])
