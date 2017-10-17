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

from exts.common import log, REDIS_NEWEST_CHARGE_MODE, DEFAULT_CHARGE_EXPIRED, DEFAULT_CHARGE_MODE
from exts.resource import db, redis_client
from service.charge.model import Charge


# 费率接口
class ChargeService(object):
    @staticmethod
    def create(name, charge_mode):

        try:

            charge = Charge(name=name,
                            charge_mode=charge_mode)

            # 更新redis中最新的费率
            redis_client.setex(REDIS_NEWEST_CHARGE_MODE, DEFAULT_CHARGE_EXPIRED, json.dumps(charge.to_dict()))

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

    # 获得最新费率
    @staticmethod
    def get_newest_charge_mode():
        # 先从redis中获取
        charge_str = redis_client.get(REDIS_NEWEST_CHARGE_MODE)
        if charge_str is not None:
            try:
                charge = json.loads(charge_str)
                charge_mode = charge.get('charge_mode')
                if isinstance(charge_mode, int) and charge_mode > 0:
                    log.info("当前从redis中获得费率: charge_mode = {}".format(charge_mode))
                    return charge_mode
                log.error("当前redis中费率数据类型不正确: charge_str = {}".format(charge_str))
            except Exception as e:
                log.error("费率解析失败: charge_str = {}".format(charge_str))
                log.exception(e)

        try:
            # 如果从redis中获取费率失败，则从数据库中获得最新费率
            charge_item = Charge.query.order_by(Charge.ctime.desc()).first()
            if charge_item is None:
                # 存储默认费率到数据库中，同时存入redis
                ChargeService.create('DEFAULT_CHARGE', DEFAULT_CHARGE_MODE)

                log.warn("当前数据库中还没有任何费率信息, 使用默认费率: DEFAULT_CHARGE_MODE = {}".format(DEFAULT_CHARGE_MODE))
                return DEFAULT_CHARGE_MODE

            # 设置费率到redis
            redis_client.setex(REDIS_NEWEST_CHARGE_MODE, DEFAULT_CHARGE_EXPIRED, json.dumps(charge_item.to_dict()))

            log.info("加载当前最新费率到redis: charge_mode = {} time = {}".format(
                charge_item.charge_mode, charge_item.ctime.strftime('%Y-%m-%d %H:%M:%S')))

            return charge_item.charge_mode
        except Exception as e:
            log.error("获取费率失败: ")
            log.exception(e)

        log.error("费率获取异常，采用默认费率: DEFAULT_CHARGE_MODE = {}".format(DEFAULT_CHARGE_MODE))
        return DEFAULT_CHARGE_MODE
