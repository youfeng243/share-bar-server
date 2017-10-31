#!/usr/bin/env python
# encoding: utf-8
''' The version file save and sync application '''
import json
import os
import sqlite3
import time

import requests
from flask import Flask, request, redirect, url_for, abort, send_from_directory, render_template
from werkzeug.contrib.fixers import ProxyFix

from exts.common import get_remote_addr, HTTP_BAD_REQUEST, fail, HTTP_FORBIDDEN, HTTP_NOT_FOUND, HTTP_SERVER_ERROR
from logger import Logger

log = Logger('file_server.log').get_logger()

UPLOAD_FOLDER = 'uploaded_files'
ALLOWED_EXTENSIONS = set(['db'])

application = Flask(__name__)

application.debug = False

application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
application.config['SECRET_KEY'] = "4&^^%%$%BJHGFGHHVVBN%$$#^"

application.wsgi_app = ProxyFix(application.wsgi_app)


def setup_error_handler(app):
    @app.errorhandler(400)
    @app.errorhandler(ValueError)
    def http_bad_request(e):
        log.warn(
            '{addr} request: {method}, '
            'url: {url}'.format(addr=get_remote_addr(),
                                method=request.method,
                                url=request.url))
        log.warn("{}".format(request.headers))
        log.exception(e)
        return fail(HTTP_BAD_REQUEST)

    @app.errorhandler(403)
    def http_forbidden(e):
        log.warn(
            '{addr} request: {method}, '
            'url: {url}'.format(addr=get_remote_addr(),
                                method=request.method,
                                url=request.url))
        log.warn("{}".format(request.headers))
        log.exception(e)
        return fail(HTTP_FORBIDDEN)

    @app.errorhandler(404)
    def http_not_found(e):
        log.warn(
            '{addr} request: {method}, '
            'url: {url}'.format(addr=get_remote_addr(),
                                method=request.method,
                                url=request.url))
        log.warn("{}".format(request.headers))
        log.exception(e)
        return fail(HTTP_NOT_FOUND)

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def http_server_error(e):
        log.warn(
            '{addr} request: {method}, '
            'url: {url}'.format(addr=get_remote_addr(),
                                method=request.method,
                                url=request.url))
        log.warn("{}".format(request.headers))
        log.exception(e)
        return fail(HTTP_SERVER_ERROR)


# 设置错误处理流程
setup_error_handler(application)


def allowed_file(filename):
    ''' File type restriction '''
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@application.route('/data/<game>/<version>', methods=['GET'])
def get_data(game, version):
    ''' Get the uploaded files'''
    name = version + '.db'
    return send_from_directory('uploaded_files/' + game, name, as_attachment=True)


def sync_game(game, version):
    ''' Synchronizing version with manage system '''
    url = 'http://weixin.doumihuyu.com/admin/device/game'
    payload = {'username': 'youfeng', 'password': '123456', 'game': game, 'version': version}

    try:
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            return '发送更新请求失败'
        return r.text
    except Exception as e:
        log.error("发送游戏信息异常:")
        log.exception(e)

    return '发送更新请求失败'


def del_game(game):
    ''' Delete on manage system '''
    url = 'http://weixin.doumihuyu.com/admin/device/game'
    payload = {'username': 'youfeng', 'password': '123456', 'game': game}

    try:
        r = requests.delete(url, json=payload)
        if r.status_code != 200:
            return '发送删除请求失败'
        return r.text
    except Exception as e:
        log.error("删除游戏信息异常:")
        log.exception(e)

    return '发送删除请求失败'


@application.route('/data/<game>', methods=['DELETE'])
def delete(game):
    ''' Delete a game '''
    if json.loads(del_game(game))['success']:
        path = os.path.join(application.config['UPLOAD_FOLDER'], game)
        for root, dirs, files in os.walk(path):
            for doc in files:
                os.remove(os.path.join(path, doc))
        return '删除成功！'
    return '删除失败！'


@application.route('/data', methods=['POST'])
def upload():
    ''' Post a .db file and save it '''
    temp_file_name = str(int(round(time.time() * 1000))) + '.db'
    base_path = application.config['UPLOAD_FOLDER']
    temp_file_path = os.path.join(base_path, temp_file_name)
    try:
        upload_file = request.files.get('data')
        if upload_file and allowed_file(upload_file.filename):

            if not os.path.exists(base_path):
                os.makedirs(base_path)

            upload_file.save(temp_file_path)
            conn = sqlite3.connect(temp_file_path)
            res = conn.execute('SELECT game, version FROM config')
            for row in res:
                game = row[0]
                version = row[1]
            conn.close()
            if not os.path.exists(os.path.join(base_path, game)):
                os.makedirs(os.path.join(base_path, game))
            os.rename(temp_file_path, os.path.join(base_path, game, version + '.db'))
            sync_res = json.loads(sync_game(game, version))['result']
            log.info('上传成功！文件名：' + game + '/' + version + '.db。—— 后台状态：' + sync_res)
            return redirect('/')
        log.info("没有提交任何文件!")
    except Exception as e:
        log.error("上传游戏信息失败:")
        log.exception(e)
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e1:
                log.error("临时文件删除失败: {}".format(temp_file_name))
                log.exception(e1)
        return redirect('/')
    return redirect('/')


@application.route('/download', methods=['POST'])
def download():
    ''' Post a JSON file and get the file which matches '''
    if request.json is None:
        return abort(404)
    game = request.json.get('game', None)
    version = request.json.get('version', None)
    if not all([game, version]):
        return abort(404)
    return redirect(url_for('get_data', game=game, version=version))


@application.route('/')
def html():
    ''' HTML interface '''
    return render_template('upload.html')


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8081)
