# -*- coding:gbk -*-
'''ʾ��4: ʹ����Ƕ��װ������ȷ��ÿ���º����������ã�
��Ƕ��װ�������βκͷ���ֵ��ԭ������ͬ��װ�κ���������Ƕ��װ��������'''


def deco(func):
    print type(func)

    def _deco(*args, **kwargs):
        print("before {} called.".format(func.func_name))
        ret = func(*args, **kwargs)
        print("after {} called.".format(func.func_name))

        return ret
        # ����Ҫ����func��ʵ����Ӧ����ԭ�����ķ���ֵ

    return _deco


@deco
def myfunc(a, b, c):
    print "a = {} b = {} c = {}".format(a, b, c)
    print(" myfunc() called.")
    return a + b + c


# test_func = deco(myfunc, 1, 2, 3)
# print test_func.func_name

print myfunc(1, 2, 3)
