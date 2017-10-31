#!/usr/bin/env python
# encoding: utf-8
''' The version file save and sync application '''
import json
import os
import sqlite3

import requests
from flask import Flask, request, redirect, url_for, abort, send_from_directory, render_template
from werkzeug.contrib.fixers import ProxyFix

UPLOAD_FOLDER = 'version_file/uploaded_files'
ALLOWED_EXTENSIONS = set(['db'])

APP = Flask(__name__)
APP.debug = False

APP.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

APP.wsgi_app = ProxyFix(APP.wsgi_app)


def allowed_file(filename):
    ''' File type restriction '''
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@APP.route('/data/<game>/<version>', methods=['GET'])
def get_data(game, version):
    ''' Get the uploaded files'''
    name = version + '.db'
    return send_from_directory('uploaded_files/' + game, name, as_attachment=True)


def sync_game(game, version):
    ''' Synchronizing version with manage system '''
    url = 'http://weixin.doumihuyu.com/admin/device/game'
    payload = {'username': 'youfeng', 'password': '123456', 'game': game, 'version': version}
    return requests.post(url, json=payload).text


def del_game(game):
    ''' Delete on manage system '''
    url = 'http://weixin.doumihuyu.com/admin/device/game'
    payload = {'username': 'youfeng', 'password': '123456', 'game': game}
    return requests.delete(url, json=payload).text


@APP.route('/data/<game>', methods=['DELETE'])
def delete(game):
    ''' Delete a game '''
    if json.loads(del_game(game))['success']:
        path = os.path.join(APP.config['UPLOAD_FOLDER'], game)
        for root, dir, files in os.walk(path):
            for doc in files:
                os.remove(os.path.join(path, doc))
        return '删除成功！'
    return '删除失败！'


@APP.route('/data', methods=['POST'])
def upload():
    ''' Post a .db file and save it '''
    upload_file = request.files['data']
    if upload_file and allowed_file(upload_file.filename):
        path = APP.config['UPLOAD_FOLDER']
        if not os.path.exists(path):
            os.makedirs(path)
        upload_file.save(os.path.join(path, 'temp.db'))
        conn = sqlite3.connect(os.path.join(path, 'temp.db'))
        res = conn.execute('SELECT game, version FROM config')
        for row in res:
            game = row[0]
            version = row[1]
        conn.close()
        if not os.path.exists(os.path.join(path, game)):
            os.makedirs(os.path.join(path, game))
        os.rename(os.path.join(path, 'temp.db'), os.path.join(path, game, version + '.db'))
        syncres = json.loads(sync_game(game, version))['result']
        return '上传成功！文件名：' + game + '/' + version + '.db。—— 后台状态：' + syncres


@APP.route('/download', methods=['POST'])
def download():
    ''' Post a JSON file and get the file which matches '''
    if request.json is None:
        return abort(404)
    game = request.json.get('game', None)
    version = request.json.get('version', None)
    if not all([game, version]):
        return abort(404)
    return redirect(url_for('get_data', game=game, version=version))


@APP.route('/')
def html():
    ''' HTML interface '''
    return render_template('upload.html')


if __name__ == '__main__':
    APP.run(host='0.0.0.0', port=8081)
