# -*- coding: utf-8 -*-


from flask import Blueprint, request

from exts.common import fail, success, log, HTTP_OK
from exts.sms import mobile_reach_ratelimit, request_sms
from tools.wechat_api import wechat_login_required

bp = Blueprint('captcha', __name__, url_prefix="/wechat")


# 请求手机验证码，进行用户注册
@bp.route('/captcha', methods=['POST'])
@wechat_login_required
def request_code():
    if not request.is_json:
        log.warn("参数错误...")
        return fail(HTTP_OK, u"need application/json!!")

    mobile = request.json.get('mobile', None)
    if mobile is None:
        return fail(HTTP_OK, u'手机号不能未空')

    if len(mobile) != 11:
        return fail(HTTP_OK, u'手机号不合法')

    if mobile_reach_ratelimit(mobile):
        return fail(HTTP_OK, u'验证码已发送')

    # 通过手机号请求验证码
    if request_sms(mobile):
        return success()

    return fail(HTTP_OK, u"发送验证码请求失败!")
