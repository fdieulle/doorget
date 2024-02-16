from doorget import cache, StorageMode, setup_disk_storage
from typing import Any
import pandas as pd
import numpy as np
import os


@cache(mode=StorageMode.Disk)
def f1(id: int) -> pd.DataFrame:
    return pd.DataFrame(np.random.normal(size=(100 * id, id)), columns=[f'C{i+1}' for i in range(id)])


@cache(mode=StorageMode.Disk)
def f2(x: pd.DataFrame, name: str) -> pd.DataFrame:
    x = x.copy()
    x['C2'] = name
    return x


@cache(mode=StorageMode.Identity)
def transform(x: pd.DataFrame) -> pd.DataFrame:
    return x.copy()


def test_simple_case(tmpdir):
    setup_disk_storage(tmpdir)

    cache_folder = os.path.join(tmpdir, 'tests.test_disk.f1')
    assert not os.path.exists(cache_folder)

    df1 = f1(1)
    assert os.path.exists(cache_folder)
    df2 = f1(2)

    assert all(df1 == f1(1))
    assert id(df1) != id(f1(1))
    assert all(df2 == f1(2))


def test_dependency(tmpdir):
    setup_disk_storage(tmpdir)

    f1_cache_folder = os.path.join(tmpdir, 'tests.test_disk.f1')
    f2_cache_folder = os.path.join(tmpdir, 'tests.test_disk.f2')
    assert not os.path.exists(f1_cache_folder)
    assert not os.path.exists(f2_cache_folder)

    df1 = f1(1)
    assert os.path.exists(f1_cache_folder)
    assert not os.path.exists(f2_cache_folder)
    df2 = f1(2)

    df1_foo = f2(df1, 'foo')
    assert os.path.exists(f1_cache_folder)
    assert os.path.exists(f2_cache_folder)
    df1_bar = f2(df1, 'bar')

    assert (df1_foo == f2(df1, 'foo')).values.all()
    assert (df1_bar == f2(df1, 'bar')).values.all()
    assert not (df1_foo == df1_bar).values.all()

    df2_foo = f2(df2, 'foo')
    df2_bar = f2(df2, 'bar')

    assert (df2_foo == f2(df2, 'foo')).values.all()
    assert (df2_bar == f2(df2, 'bar')).values.all()
    assert not (df2_foo == df2_bar).values.all()

    
def test_dependency_with_transform_in_between(tmpdir):
    setup_disk_storage(tmpdir)

    f1_cache_folder = os.path.join(tmpdir, 'tests.test_disk.f1')
    f2_cache_folder = os.path.join(tmpdir, 'tests.test_disk.f2')
    transform_cache_folder = os.path.join(tmpdir, 'tests.test_disk.transform')
    assert not os.path.exists(f1_cache_folder)
    assert not os.path.exists(f2_cache_folder)
    assert not os.path.exists(transform_cache_folder)

    df1 = f1(10) # key = f1(10)
    assert os.path.exists(f1_cache_folder)
    assert not os.path.exists(f2_cache_folder)
    assert not os.path.exists(transform_cache_folder)

    df1_copy = transform(df1) # key = transform(f1(10))
    assert os.path.exists(f1_cache_folder)
    assert not os.path.exists(f2_cache_folder)
    assert not os.path.exists(transform_cache_folder)

    df1_foo = f2(df1_copy, 'foo') # key = f2(transform(f1(10)),foo)
    assert os.path.exists(f1_cache_folder)
    assert os.path.exists(f2_cache_folder)
    assert not os.path.exists(transform_cache_folder)

    assert (df1_foo == f2(df1_copy, 'foo')).values.all()
    assert not (df1_foo == df1_copy).values.all()

    assert (df1_foo == f2(df1, 'foo')).values.all()
    assert not (df1_foo == df1_copy).values.all()

    assert not os.path.exists(transform_cache_folder)

