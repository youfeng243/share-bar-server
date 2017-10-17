#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: impl.py
@time: 2017/10/17 21:51
"""
import json

from sqlalchemy.exc import IntegrityError

from exts.common import log, REDIS_NEWEST_CHARGE_MODE
from exts.resource import db, redis_client
from service.charge.model import Charge


# 费率接口
class ChargeService(object):
    @staticmethod
    def create(name, charge_mode):

        charge = Charge(name=name,
                        charge_mode=charge_mode)

        # 更新redis中最新的费率
        redis_client.set(REDIS_NEWEST_CHARGE_MODE, json.dumps(charge.to_dict()))

        try:
            db.session.add(charge)
            db.session.commit()
        except IntegrityError:
            log.error("主键重复: name = {} charge_mode = {}".format(
                name, charge_mode))
            db.session.rollback()
            return None, False
        except Exception as e:
            log.error("未知插入错误: name = {} charge_mode = {}".format(
                name, charge_mode))
            log.exception(e)
            return None, False
        return charge, True
