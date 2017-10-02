# -*- coding:gbk -*-
'''示例4: 使用内嵌包装函数来确保每次新函数都被调用，
内嵌包装函数的形参和返回值与原函数相同，装饰函数返回内嵌包装函数对象'''


def deco(func):
    print type(func)

    def _deco(*args, **kwargs):
        print("before {} called.".format(func.func_name))
        ret = func(*args, **kwargs)
        print("after {} called.".format(func.func_name))

        return ret
        # 不需要返回func，实际上应返回原函数的返回值

    return _deco


@deco
def myfunc(a, b, c):
    print "a = {} b = {} c = {}".format(a, b, c)
    print(" myfunc() called.")
    return a + b + c


# test_func = deco(myfunc, 1, 2, 3)
# print test_func.func_name

print myfunc(1, 2, 3)
