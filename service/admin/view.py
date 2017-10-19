#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/2 19:33
"""
from flask import Blueprint
from flask import g
from flask import request
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from exts.common import success, log, fail, HTTP_OK
from service.admin.model import Admin
from service.role.model import Role

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.before_request
def before_request():
    g.admin = current_user


# 登录
@bp.route('/sign_in', methods=['POST'])
def login():
    if g.admin is not None and g.admin.is_authenticated:
        return success(u"账户已经登录!")

    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username is None or password is None:
        log.warn("用户账号密码没有传过来...username = {} password = {}".format(
            username, password))
        return fail(HTTP_OK, u"没有用户密码信息!")

    # 获取是否需要记住密码
    is_remember = request.json.get('remember', False)

    admin = Admin.query.authenticate(username, password)
    if admin is not None:
        # 判断账户是否被停用
        if not admin.is_active():
            return fail(HTTP_OK, u'账户已被暂停使用,请联系管理员')

        if is_remember:
            login_user(admin, remember=True)
        else:
            login_user(admin, remember=False)
        log.info("用户登录成功: {} {}".format(username, password))
        return success(u'登录成功')

    admin = Admin.get_by_username(username)
    if admin is None:
        return fail(HTTP_OK, u'用户不存在')
    return fail(HTTP_OK, u'用户名或密码错误，请重新登陆!')


# 编辑管理员信息
@bp.route('', methods=['PUT'])
@login_required
def update():
    # 只支持修改 名称 与 启用状态
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    # 判断当前管理员是否为超级管理员，只有超级管理员才有修改管理员信息的权限
    if current_user.role.name != Role.SUPER_ADMIN:
        return fail(HTTP_OK, u"没有操作权限，只有超级管理员才能够编辑管理员信息...!")

    a_id = request.json.get('id', None)
    if a_id is None:
        log.warn("没有传入管理员id信息")
        return fail(HTTP_OK, u"没有传入管理员id信息!")

    admin = Admin.get(a_id)
    if admin is None:
        log.warn("当前ID信息不存在: id = {}".format(a_id))
        return fail(HTTP_OK, u"当前ID信息不存在!")

    name = request.json.get('name', None)
    if isinstance(name, basestring) and name.strip() != '':
        admin.name = name
    elif name is not None:
        log.warn("name信息不正确，不是字符串或为空字符串! name = {}".format(name))
        return fail(HTTP_OK, u"name信息不正确，不是字符串或为空字符串!")

    state = request.json.get('state', None)
    if state is not None:

        if g.admin.id == a_id:
            return fail(HTTP_OK, u"不能修改自身状态信息")

        if state in Admin.STATUS_VALUES:
            admin.state = state
        else:
            log.warn("state 状态信息不正确! state = {}".format(state))
            return fail(HTTP_OK, u"state 状态信息不正确!")

    # 判断存储是否正确
    if not admin.save():
        log.warn("管理员信息存储失败!!!")
        return fail(HTTP_OK, u"管理员信息存储失败!")

    log.info("管理员信息修改成功: {}".format(admin.to_dict()))
    return success(admin.to_dict())


# 添加管理员
@bp.route('', methods=['POST'])
@login_required
def new_admin():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    # 判断当前管理员是否为超级管理员，只有超级管理员才有修改管理员信息的权限
    if current_user.role.name != Role.SUPER_ADMIN:
        return fail(HTTP_OK, u"没有操作权限，只有超级管理员才能够编辑管理员信息...!")

    name = request.json.get('name', None)
    username = request.json.get('username', None)
    role_id = request.json.get("role_id", None)
    password = request.json.get("password", None)

    if name is None or username is None or role_id is None or password is None:
        return fail(HTTP_OK, u"添加管理员参数不正确...!")

    # 查找当前用户名是否已经被占用了
    if Admin.get_by_username(username) is not None:
        return fail(HTTP_OK, u"该用户名已被使用...!")

    # 创建并添加管理员
    admin, is_success = Admin.create(username, password, name, role_id)
    if admin is None:
        log.warn("管理员信息添加失败")
        return fail(HTTP_OK, u"管理员信息添加失败!")

    log.info("管理员信息添加成功: {}".format(admin.to_dict()))
    return success(admin.to_dict())


# 分页查询所有管理员接口
@bp.route('/list', methods=['POST'])
@login_required
def get_admin_list():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    page = request.json.get('page')
    size = request.json.get('size')

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

    return success(Admin.get_admin_list(page, size))


# 登出
@bp.route('/sign_out', methods=['GET'])
@login_required
def logout():
    logout_user()
    return success(u"登出成功!")


# 测试用
@bp.route('/test', methods=['GET'])
@login_required
def test():
    log.info("当前属于登录状态...")
    return success(u"测试通过!")
