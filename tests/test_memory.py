from doorget import cache, StorageMode
from typing import Any
import pandas as pd
import numpy as np

@cache
def f1(id: int) -> pd.DataFrame:
    return pd.DataFrame(np.random.normal(size=(100 * id, id)), columns=[f'C{i+1}' for i in range(id)])

@cache
def f2(x: pd.DataFrame, name: str) -> pd.DataFrame:
    x = x.copy()
    x[name] = 1.0
    return x

@cache(mode=StorageMode.Identity)
def transform(x: pd.DataFrame) -> pd.DataFrame:
    return x.copy()


def test_simple_case():
    df1 = f1(1)
    df2 = f1(2)

    assert all(df1 == f1(1))
    assert id(df1) == id(f1(1))

    assert id(df1) != id(df2)

    assert all(df2 == f1(2))
    assert id(df2) == id(f1(2))

def test_dependency():
    df1 = f1(1)
    df2 = f1(2)

    df1_foo = f2(df1, 'foo')
    df1_bar = f2(df1, 'bar')

    assert all(df1_foo == f2(df1, 'foo'))
    assert id(df1_foo) == id(f2(df1, 'foo'))

    assert id(df1_foo) != id(df1_bar)

    assert all(df1_bar == f2(df1, 'bar'))
    assert id(df1_bar) == id(f2(df1, 'bar'))

    df2_foo = f2(df2, 'foo')
    df2_bar = f2(df2, 'bar')

    assert id(df1_foo) != id(df2_foo)
    assert id(df1_foo) != id(df2_bar)
    assert id(df1_bar) != id(df2_bar)

    assert all(df2_foo == f2(df2, 'foo'))
    assert id(df2_foo) == id(f2(df2, 'foo'))

    assert id(df2_foo) != id(df2_bar)

    assert all(df2_bar == f2(df2, 'bar'))
    assert id(df2_bar) == id(f2(df2, 'bar'))

    
def test_dependency_with_transform_in_between():
    df1 = f1(10) # key = f1(10)

    df1_copy = transform(df1) # key = transform(f1(10))

    df1_foo = f2(df1_copy, 'foo') # key = f2(transform(f1(10)),foo)

    assert all(df1_foo == f2(df1_copy, 'foo'))
    assert id(df1_foo) == id(f2(df1_copy, 'foo'))

    assert all(df1_foo == f2(df1, 'foo'))
    assert id(df1_foo) != id(f2(df1, 'foo'))

class Foo:
    def __init__(self, data: Any):
        self.data = data

@cache
def f_no_args() -> Foo:
    return Foo(None)

@cache
def f_with_arg(arg) -> Foo:
    return Foo([arg])

@cache
def f_with_args(arg1, arg2, arg3) -> Foo:
    return Foo([arg1, arg2, arg3])

@cache
def f_with_default_value(id: int=10) -> Foo:
    return Foo([id])

def test_in_memory_no_args():
    r1 = f_no_args()
    assert r1 is not None
    assert r1.data is None

    r2 = f_no_args()
    assert r1 == r2
    assert id(r1) == id(r2)
    assert r2.data is None

def test_in_memory_with_arg():
    arg = 'Hello world'

    r1 = f_with_arg(arg)
    assert r1.data[0] == arg

    r2 = f_with_arg(arg)
    assert r2 == r1
    assert r2.data[0] == arg

    r3 = f_with_arg('Hello world')
    assert r3 == r1
    assert r3.data[0] == arg

    r4 = f_with_arg('Hello new world')
    assert r4 != r1
    assert r4.data[0] == 'Hello new world'

def test_in_memory_with_args():
    arg1 = 'Hello'
    arg2 = ' world '
    arg3 = '!'

    r1 = f_with_args(arg1, arg2, arg3)
    assert r1.data[0] == arg1
    assert r1.data[1] == arg2
    assert r1.data[2] == arg3

    r2 = f_with_args(arg1, arg2, arg3=arg3)
    assert r2 == r1
    assert r2.data[0] == arg1
    assert r2.data[1] == arg2
    assert r2.data[2] == arg3

    r3 = f_with_args('Hello', arg2=' world ', arg3='!')
    assert r3 == r1
    assert r3.data[0] == arg1
    assert r3.data[1] == arg2
    assert r3.data[2] == arg3

    r4 = f_with_args('Hello', arg2=' new world ', arg3=arg3)
    assert r4 != r1
    assert r4.data[0] == arg1
    assert r4.data[1] == ' new world '
    assert r4.data[2] == arg3

def test_in_memory_with_list_and_dict_args():
    arg1 = [1, 2, 3]
    arg2 = {'key1': 123, 'key2': 'foo'}
    arg3 = [1, {'k1': [1,2], 'k2': {1:1, 2:2}}, [1,[1,2],3]]

    r1 = f_with_args(arg1, arg2, arg3)
    assert r1.data[0] == arg1
    assert r1.data[1] == arg2
    assert r1.data[2] == arg3

    r2 = f_with_args(arg1, arg2, arg3)
    assert r2 == r1
    assert r2.data[0] == arg1
    assert r2.data[1] == arg2
    assert r2.data[2] == arg3

def test_in_memory_with_arg_with_default_value():
    r1 = f_with_default_value()
    r2 = f_with_default_value(10)
    r3 = f_with_default_value(id=10)
    r4 = f_with_default_value(20)
    r5 = f_with_default_value(id=20)

    assert id(r1) == id(r2)
    assert id(r1) == id(r3)
    assert id(r1) != id(r4)
    assert id(r5) == id(r4)