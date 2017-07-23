#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper
import functools


def disable(func):
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:
    '''
    return func


def decorator(decor):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''
    @functools.wraps(decor)
    def wrapper(func):
        return update_wrapper(decor(func), func)
    return wrapper


@decorator
def countcalls(func):
    '''Decorator that counts calls made to the function decorated.'''
    def wrapper(*args, **kwargs):
        wrapper.cnt += 1
        return func(*args, **kwargs)
    return wrapper


def memo(func):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''
    cache = {}
    @functools.wraps(func)
    def inner(*args, **kwargs):
        key = args, kwargs
        if key not in cache:
            cache[key] = func(*args, **kwargs)
            return cache[key]
    return inner


def n_ary(func):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''
    def wrapper_f(x, *args):
        return x if not args else func(x, wrapper_f(*args))
    return wrapper_f

def trace(template):
    '''Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    '''
    @decorator
    def trace_decor(func):
        def trace_wrapper(*args):
            call_representation = '{0}({1})'.format(func.__name__, ', '.join(map(repr, args)))
            indent = trace_wrapper.level * template
            print '{0}-->{1}'.format(indent, call_representation)
            trace_wrapper.level +=1
            try:
                res = func(*args)
                indent = (trace_wrapper.level-1) * template
                print '{0} <-- {1} == {2}'.format(indent, call_representation, res)
            finally:
                trace_wrapper.level-=1
            return res
        trace_wrapper.level = 0
        return trace_wrapper
    return trace_decor


@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("####")
@memo
def fib(n):
    return 1 if n <= 1 else fib(n-1) + fib(n-2)




def main():
    print foo(4, 3)
    print foo(4, 3, 2)
    print foo(4, 3)
    print "foo was called", foo.calls, "times"

    print bar(4, 3)
    print bar(4, 3, 2)
    print bar(4, 3, 2, 1)
    print "bar was called", bar.calls, "times"

    print fib.__doc__
    fib(3)
    print fib.calls, 'calls made'


if __name__ == '__main__':
    main()
