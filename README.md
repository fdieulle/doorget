# doorget

Python package which memoizes functions with a support of data dependencies. 
It can be adapt to your code with a low touch by using the `cache` decorator 
on any function to enable the memoization.

## Memoization

> In computing, memoization or memoisation is an optimization technique used primarily to speed up computer programs by storing the results of expensive function calls to pure functions and returning the cached result when the same inputs occur again. Memoization has also been used in other contexts, such as in simple mutually recursive descent parsing. [Wikipedia](https://en.wikipedia.org/wiki/Memoization) 


```{python}
from doorget import cache
import panda as pd

@cache
def fetch(name: str) -> pd.DataFrame:
    pass

foo = fetch('foo') # The function is called
foo_again = fetch('foo') # The function is not called, the previous returned data is read from the cache instead
bar = fetch('bar') # The function is called because the input is not known yet
```

## Storage modes

The package propose you 3 built in storage modes and also to provide any other custom storage.

* `Memory`: The fastest mode.
* `Disk`: The unlimited mode.
* `Identity` This mode is a helper for data [dependencies](#data_dependencies) and [cascades](#cascade_data_identity)
* `Custom`: Your best mode

### Memory

This is the default storage which caches all returned data in memory. This is the fastest way to retreive  data
from an existing input. But this mode has 3 caveats. The first caveat is that the data is cached within your current process only. After your process ends all cached data will be lost. It avoids you sharing the cached data between processes as well. The second caveat is the limited memory constrained by your hardware to couple of Giga Bytes maximum.

```{python}
from doorget import cache, StorageMode
import panda as pd


@cache # Memory by default
def foo(name: str) -> pd.DataFrame:
    pass

@cache(mode=StorageMode.Memory)
def bar(name: str) -> pd.DataFrame:
    pass

```

### Disk

This is the most common usage af the memoization. It is slower than the `Memory` mode because the data is read from
the disk but it solves the 2 caveats. To improve the speed the `Disk` mode use the parquet format if a pandas `DataFrame`
is returned, pickle otherwise.

If no cache folder is specified, the default is used instead. the function and its module name are used as sub folder to guarantie an unique storage location. The default folder can be change at any time with the function `setup_disk_storage` 

```{python}
from doorget import cache, StorageMode
import panda as pd


@cache(mode=StorageMode.Disk) # Use the default folder
def fetch_default(name: str) -> pd.DataFrame:
    pass

@cache(mode=StorageMode.Disk, cache_folder='./my_custom/folder/bar')
def fetch_custom(name: str) -> pd.DataFrame:
    pass


fetch_default('foo')
fetch_custom('bar')

setup_disk_storage('./my_default/folder')
fetch_default('foo') # Function call because the cache folder changed
fetch_custom('bar') # Data read
```

### Custom

When you specify this mode you have to specify the `storage` argument as well. It allows to defin any knid of storage which could fits better your use case, for performances, infrastructure, sharing, ... purpose.

Your custom storage is required to inherit from the `Storage` class.

```
from typing import Any, List
from dataclasses import dataclass
from doorget import CacheKey

@dataclass
class Storage:
    name: str

    # Core functions
    def contains(self, key: CacheKey) -> bool:
        pass
    def fetch(self, key: CacheKey) -> Any:
        pass
    def store(self, key: CacheKey, data: Any) -> None:
        pass

    # Cache management helpers
    def clear(self) -> None:
        pass
    def remove(self, key: CacheKey) -> bool:
        pass
    def keys(self) -> List[CacheKey]:
        pass
```

## Data dependencies

The added value from a simple memoized function is the carry of data dependencies. When a complex object like a pandas DataFrame is passed as an argument, it is not used directly to build the key, but substitued with its own memoized key.

```{python}
from doorget import cache
import panda as pd

@cache
def fetch(name: str) -> pd.DataFrame:
    pass

@cache
def fetch(df: pd.DataFrame, scope: str) -> pd.DataFrame:
    pass

df = fetch('foo') # key for df => "fetch('foo')"
summary = summarize(df, 'daily') # key for summary => "summarize(fetch('foo'), 'daily')"

```

Under the hood a memoized function keep a track of any object reference (Identity in python) returned by attaching its 
memoized key. If the function returns a `Tuple`, the contained items are tracked as well.


## Cascade data identity

Sometime it is faster to transform a data than memoizing it. If this transformed data is used as aan argument for another memoized function, the data dependency is lost. To not break the data dependencies you can isolate you can isolate your
data transformation in a memoized function with the `Identity` storage mode.

```{python}
@cache(mode=StorageMode.Identity)
def transform(x: pd.DataFrame) -> pd.DataFrame:
    return x.copy()

df = fetch('foo') # key for df => "fetch('foo')"
df_copy = transform(df) # key for df_copy => "transform(fetch('foo'))"

summary = summarize(df_copy, 'daily') # key for summary => "summarize(transform(fetch('foo')), 'daily')"
```

## Administrate your caches

The package provides you some backdoors to administrate your caches and more precisely your storages.

* `list_memory_storages()`
* `list_disk_storages()`
* `list_custom_storages()`

Each memoized function has its owned storage. From a storage you can list all the contained keys, but also 
remove some or clear them all. A function call is stored in a `CacheKey` object which represents the function
called with its input combination as a `Tuple`. If the key has data depedencies the dependencies are nested
by using `Tuple` recursively.  