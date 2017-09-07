# coding:utf-8
import logging
import os
import sys

from cloghandler import ConcurrentRotatingFileHandler

PY3k = sys.version_info >= (3,)
if not PY3k:
    reload(sys)
    sys.setdefaultencoding('utf-8')


class Logger(object):
    # 默认info级别
    level = logging.INFO

    # 存放目录名称
    folder = 'log'

    def __init__(self, filename):
        pwd = os.path.abspath(os.path.dirname(__file__))

        directory = os.path.join(pwd, self.folder)
        if not os.path.exists(directory):
            os.mkdir(directory)

        self.file_path = directory + '/' + filename

        self.log = logging.getLogger(filename)
        self.log.setLevel(self.level)

        handler = ConcurrentRotatingFileHandler(self.file_path, 'a', 1024 * 1024 * 100, backupCount=5, encoding='utf-8')
        # handler.suffix = "%Y-%m-%d"

        # 设置输出格式
        # format_log = "%(asctime)s %(threadName)s %(funcName)s %(filename)s:%(lineno)s %(levelname)s %(message)s"
        formatter = logging.Formatter(
            '%(asctime)s [%(processName)s %(threadName)s %(levelname)s %(module)s:%(funcName)s:%(lineno)d] %(message)s')
        # fmt = logging.Formatter(formatter)
        handler.setFormatter(formatter)

        self.log.addHandler(handler)

        # 控制台输出
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)

        self.log.addHandler(stream)

    def set_level(self, level):
        self.log.setLevel(level=level)
        return self.log

    def get_logger(self):
        return self.log


if __name__ == '__main__':
    log = Logger('log.log').get_logger()
    log.info('text')
    log.error('text')
