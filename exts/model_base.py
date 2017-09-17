#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: common.py
@time: 2017/8/28 20:58
"""
import json
from datetime import datetime

from flask import request

from exts.common import log, fail, HTTP_OK, success, package_result
from exts.database import db


class ModelBase(db.Model):
    __abstract__ = True

    # ID
    id = db.Column(db.Integer, primary_key=True)

    # 生效时间 创建时间
    ctime = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    # 数据更新时间
    utime = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    def delete(self):
        try:
            if hasattr(self, 'deleted'):
                self.deleted = True
                db.session.add(self)
            else:
                db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            log.error("未知删除错误: {}".format(json.dumps(self.to_dict(), ensure_ascii=False)))
            log.exception(e)
            return False
        return True

    @classmethod
    def find_list(cls, city, area, start_time, end_time, state, page, size):
        # 条件查询
        query = cls.query

        # 判断是否由deleted字段，去除掉已经删除的数据信息
        if hasattr(cls, 'deleted'):
            query = query.filter(cls.deleted == False)

        # 根据状态查询
        if hasattr(cls, 'state') and state is not None:
            query = query.filter(cls.state == state)

        # 根据城市查询
        if city is not None and hasattr(cls, 'city'):
            query = query.filter(cls.city == city)

            # 在有城市的前提下按区域查询
            if area is not None and hasattr(cls, 'area'):
                query = query.filter(cls.area == area)

        # 根据时间查询
        if start_time is not None and end_time is not None:
            query = query.filter(cls.ctime.between(start_time, end_time))
        elif start_time is not None:
            query = query.filter(cls.ctime >= start_time)
        elif end_time is not None:
            query = query.filter(cls.ctime <= end_time)

        pagination = query.paginate(
            page=page,
            per_page=size,
            error_out=False)

        if pagination is None:
            return 0, None

        # 获取数据总数目
        total = query.count()
        return total, pagination.items

    # 根据条件进行搜索
    @classmethod
    def search_list(cls):
        if not request.is_json:
            log.warn("参数错误...")
            return fail(HTTP_OK, u"need application/json!!")

        page = request.json.get('page')
        size = request.json.get('size')
        city = request.json.get('city')
        area = request.json.get('area')
        start_time_str = request.json.get('start_time')
        end_time_str = request.json.get('end_time')
        state = request.json.get('state')

        # 如果存在状态信息，但是状态错误，则返回错误
        if hasattr(cls, 'state') and state is not None:
            if hasattr(cls, 'STATE_VALUES') and state not in cls.STATE_VALUES:
                return fail(HTTP_OK, u'状态信息错误!')

        if isinstance(start_time_str, basestring) and isinstance(end_time_str, basestring):
            if end_time_str < start_time_str:
                return fail(HTTP_OK, u"时间区间错误: start_time = {} > end_time = {}".format(start_time_str, end_time_str))

        try:
            # 转换为 datetime 类型
            start_time = None
            if isinstance(start_time_str, basestring):
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                log.info("转换后时间: start_time = {} type = {}".format(start_time, type(start_time)))
            else:
                log.info("start_time 不是字符串: {}".format(start_time_str))

            end_time = None
            if isinstance(end_time_str, basestring):
                end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                log.info("转换后时间: end_time = {} type = {}".format(end_time, type(end_time)))
            else:
                log.info("end_time 不是字符串: {}".format(end_time_str))
        except Exception as e:
            log.error("时间格式转换错误: start_time_str = {} end_time_str = {}".format(start_time_str, end_time_str))
            log.exception(e)
            return fail(HTTP_OK, u"时间格式转换错误!")

        if not isinstance(page, int) or \
                not isinstance(size, int):
            log.warn("请求参数错误: page = {} size = {}".format(page, size))
            return fail(HTTP_OK, u"请求参数错误")

            # 请求参数必须为正数
        if page <= 0 or size <= 0:
            msg = "请求参数错误: page = {} size = {}".format(
                page, size)
            log.error(msg)
            return fail(HTTP_OK, msg)

        if size > 50:
            log.info("翻页最大数目只支持50个, 当前size超过50 size = {}!".format(size))
            size = 50
        total, item_list = cls.find_list(city, area, start_time, end_time, state, page, size)
        if total <= 0 or item_list is None:
            return success(package_result(0, []))
        return success(package_result(total, [item.to_dict() for item in item_list]))

    @classmethod
    def get(cls, a_id):
        return cls.query.get(a_id)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    def save(self):
        self.utime = datetime.now()

        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            log.error("未知存储错误: {}".format(json.dumps(self.to_dict(), ensure_ascii=False)))
            log.exception(e)
            return False
        return True

    # 字典转换接口 必须实现
    def to_dict(self):
        raise NotImplementedError
