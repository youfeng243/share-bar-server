#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: lock_demo.py
@time: 2017/9/28 22:54
"""


def lock(func):
    print("this is wrapper")

    def decorate(*args, **kwargs):
        print '装饰器代理测试...'
        # print '参数 a = {}'.format(a)
        func(*args, **kwargs)
        print '装饰器结束...'

    return decorate


@lock
def demo():
    print 1111

demo1 = lock(demo)

print demo1.__name__
print demo.__name__

def main():
    demo()


# if __name__ == '__main__':
#     main()
