#!/usr/bin/env bash

HOST_NAME="127.0.0.1"
PORT="3306"
USERNAME="root"
PASSWORD="doumihuyuqaz"

DBNAME="share_bar_db"
create_db_sql="create database IF NOT EXISTS ${DBNAME} default character set utf8mb4 collate utf8mb4_unicode_ci"


# 安装redis
apt-get install -y redis-server
apt-get install -y git

# 安装mysql
apt-get install -y mysql-server mysql-client libmysqlclient-dev

mysql -h${HOST_NAME}  -P${PORT}  -u${USERNAME} -p${PASSWORD} -e "${create_db_sql}"

pip install virtualenv

virtualenv .venv -p python2
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

# 创建表
.venv/bin/python manage.py syncdb
echo "环境初始化完成..."