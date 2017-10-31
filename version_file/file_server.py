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

UPLOAD_FOLDER = 'uploaded_files'
ALLOWED_EXTENSIONS = set(['db'])

application = Flask(__name__)
application.debug = False

application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

application.wsgi_app = ProxyFix(application.wsgi_app)


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
    return requests.post(url, json=payload).text


def del_game(game):
    ''' Delete on manage system '''
    url = 'http://weixin.doumihuyu.com/admin/device/game'
    payload = {'username': 'youfeng', 'password': '123456', 'game': game}
    return requests.delete(url, json=payload).text


@application.route('/data/<game>', methods=['DELETE'])
def delete(game):
    ''' Delete a game '''
    if json.loads(del_game(game))['success']:
        path = os.path.join(application.config['UPLOAD_FOLDER'], game)
        for root, dir, files in os.walk(path):
            for doc in files:
                os.remove(os.path.join(path, doc))
        return '删除成功！'
    return '删除失败！'


@application.route('/data', methods=['POST'])
def upload():
    try:
        ''' Post a .db file and save it '''
        upload_file = request.files.get('data')
        if upload_file and allowed_file(upload_file.filename):
            path = application.config['UPLOAD_FOLDER']
            if not os.path.exists(path):
                os.makedirs(path)
            temp_file_name = str(int(round(time.time() * 1000))) + '.db'
            upload_file.save(os.path.join(path, temp_file_name))
            conn = sqlite3.connect(os.path.join(path, temp_file_name))
            res = conn.execute('SELECT game, version FROM config')
            for row in res:
                game = row[0]
                version = row[1]
            conn.close()
            if not os.path.exists(os.path.join(path, game)):
                os.makedirs(os.path.join(path, game))
            os.rename(os.path.join(path, temp_file_name), os.path.join(path, game, version + '.db'))
            syncres = json.loads(sync_game(game, version))['result']
            return '上传成功！文件名：' + game + '/' + version + '.db。—— 后台状态：' + syncres
    except Exception as e:
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
