#!/usr/bin/env bash

project=share-bar-server
config=gun.config.py

start() {
	status
	if [  $? = 1 ]; then
		echo "${project} is already running.."
		return 1
	fi

    mkdir -p log
    pip install virtualenv
    virtualenv .venv -p python2
    .venv/bin/pip install -U pip
    .venv/bin/pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
    .venv/bin/gunicorn -c ${config} wsgi:application
    echo "启动share-bar-server"

    # 启动access_token进程
    nohup .venv/bin/python background_process.py > /dev/null 2>&1 &
    echo "启动后台缓存处理进程.."

    cd version_file
    mkdir -p log
    virtualenv .venv -p python2
    .venv/bin/pip install -U pip
    .venv/bin/pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

    .venv/bin/gunicorn -c ${config} file_server:application

    # nohup .venv/bin/python file_server.py > /dev/null 2>&1 &
    echo "启动文件服务器.."
    echo "${project} start success..."
}

stop() {
	status
	if [ $? = 0 ]; then
	    echo "${project} not running.."
	    return 0
	fi

    ps -ef | grep -v grep | grep 'wsgi:application' | awk '{print $2}' | xargs kill -9
    rm -rf ${project}.pid

    ps -ef | grep -v grep | grep 'background_process' | grep python | awk '{print $2}' | xargs kill -9

    ps -ef | grep -v grep | grep 'file_server:application' | awk '{print $2}' | xargs kill -9

	echo "${project} stop success..."
	return 1
}

restart() {
    stop
    sleep 1
    start
}

status() {
    pid=`ps -ef | grep -v grep | grep 'wsgi:application' | awk '{print $2}'`
    if [ -z "${pid}" ]; then
        return 0
    fi
    echo "----wsgi:application----"
    echo ${pid}

    pid=`ps -ef | grep -v grep | grep 'file_server:application' | awk '{print $2}'`
    if [ -z "${pid}" ]; then
        return 0
    fi
    echo "----file_server:application----"
    echo ${pid}

    pid=`ps -ef | grep -v grep | grep 'background_process' | grep python | awk '{print $2}'`
    if [ -z "${pid}" ]; then
        return 0
    fi
    echo "----background_process----"
    echo ${pid}

    return 1
}

clean() {
    rm -rf log/*.log
    rm -rf log/*.pid
}

case "$1" in
	start|stop|restart|status|clean)
  		$1
		;;
	*)
		echo $"Usage: $0 {start|stop|status|restart|clean}"
		exit 1
esac
