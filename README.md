# doorget

[![build](https://github.com/fdieulle/doorget/actions/workflows/build.yml/badge.svg)](https://github.com/fdieulle/doorget/actions/workflows/build.yml)
[![release](https://github.com/fdieulle/doorget/actions/workflows/release.yml/badge.svg)](https://github.com/fdieulle/doorget/actions/workflows/release.yml)

[![license](https://img.shields.io/badge/license-MIT-blue.svg?maxAge=3600)](./LICENSE) 
[![pypi](https://img.shields.io/pypi/v/doorget.svg)](https://pypi.org/project/doorget/)
[![python supported](https://img.shields.io/pypi/pyversions/doorget.svg)](https://pypi.org/project/doorget/)

Python package which memoizes functions and supports data dependencies across them.
With the `cache` decorator the memoization of your code is low touch.

## Memoization

### Definition

> In computing, memoization or memoisation is an optimization technique used primarily to speed up computer programs by storing the results of expensive function calls to pure functions and returning the cached result when the same inputs occur again. Memoization has also been used in other contexts, such as in simple mutually recursive descent parsing. [Wikipedia](https://en.wikipedia.org/wiki/Memoization) 

### Example

```python
from doorget import cache
import panda as pd

@cache
def fetch(name: str) -> pd.DataFrame:
    pass

# do it
foo = fetch('foo') # The function is called
# get it
foo_again = fetch('foo') # The previous returned data is read from the cache and the function is not called.
# do it
bar = fetch('bar') # The function is called because the input is not known yet
```

## Storage modes

The package propose you 3 built in storage modes and the ability to proivde your customized storages.

* `Memory`: The fastest mode.
* `Disk`: The unlimited mode.
* `Identity` The tracker mode for data [dependencies](#data_dependencies) and [cascades](#cascade_data_identity).
* `Custom`: Your best mode.

### Memory

The memory storage use the RAM memory to memoize data.

This is the default storage mode. It is the fastest way to retreive  data from an existing input. 
But this mode has 2 caveats. The first caveat is that the data is cached within your current process only. Once your process ends all cached data are lost. It avoids you sharing the cached data between processes neither. The second caveat is the limited memory, constrained by your hardware to a couple of Giga Bytes maximum.

```python
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

The disk storage use the disk to memoize data.

This is the most common usage of the memoization. It is slower than the `Memory` mode because the data is read from
the disk but it solves the 2 caveats. The built in `Disk` mode uses `parquet` format if a pandas `DataFrame`
is returned, `pickle` otherwise.

If no cache folder is specified, a global folder is used instead. When the global folder is prefered, a sub folder is created by function from its name and module to guaranty an unique storage location. 

The global folder can change at any time with the function `setup_disk_storage`.

```python
from doorget import cache, StorageMode, setup_disk_storage
import panda as pd


@cache(mode=StorageMode.Disk) # Use the global folder
def fetch_default(name: str) -> pd.DataFrame:
    pass

@cache(cache_folder='./my_custom/folder/bar') # Overrides the global folder
def fetch_custom(name: str) -> pd.DataFrame:
    pass

# do it
fetch_default('foo')
# do it
fetch_custom('bar')

setup_disk_storage('./my_default/folder')

# do it
fetch_default('foo') # Function is called because the cache folder changed
# get it
fetch_custom('bar') # The function is not called because the custom folder is unchanged
```

### Custom

The custom storage allows you to provide you own cache where the data is memoized.

When you specify this mode you have to specify the `storage` argument. This argument takes any kind of storage which could fits better your use case, for performances, infrastructure, sharing, ... purpose.

Your custom storage imlplementation must inherit from the `Storage` class.

```python
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

## Data dependency

The added value from a simple memoized package is the carrying of data dependencies. 

When a complex object, like a pandas `DataFrame`, is passed as an argument, a simple memoization won't work.
With `doorget` when a complex object is passed as an argument, it is not used directly to build the key, but substitued with its own memoized key.

```python
from doorget import cache
import panda as pd

@cache
def fetch(name: str) -> pd.DataFrame:
    pass

@cache
def summarize(by: str, df: pd.DataFrame) -> pd.DataFrame:
    pass

df = fetch('foo') # key for df: <fetch('foo')>
summary = summarize('date', df) # key for summary: <summarize(<fetch('foo')>, 'daily')>

```

Under the hood a memoized function keep a track of any object reference (Identity in python) returned by attaching its 
memoized key. If the function returns a `Tuple`, the contained items are tracked as well.


## Cascade data identity

Sometime it is faster to transform a data than memoizing it. If this transformed data is used as an argument for another memoized function, the data dependency is lost. To avoid breaking a dependency, you can isolate your
data transformation within a memoized function with the `Identity` storage mode. It will carry no additional storage
than what your program is currently using. Under the hood the data graph is tracked by their references or `Identity`
in python.

```python
from doorget import cache, StorageMode
import panda as pd

@cache(mode=StorageMode.Identity)
def transform(x: pd.DataFrame) -> pd.DataFrame:
    return x.copy()

df = fetch('foo') # key for df: <fetch('foo')>
df_copy = transform(df) # key for df_copy: <transform(<fetch('foo')>)>

summary = summarize('date', df_copy) # key for summary: <summarize(<transform(<fetch('foo')>)>, 'daily')>
```

## Administrate your caches

The package provides you some backdoors to administrate your caches and more precisely your storages.

* `list_memory_storages()`
* `list_disk_storages()`
* `list_custom_storages()`

Each memoized function has its owned storage list. From a storage you can list all the contained keys,  
remove some items or clear them all. A function call, is stored in a `CacheKey` object. A `CacheKey` object 
contains the function name with its arguments combination as a `Tuple`. If the key has data depedencies, 
the dependencies are nested by using `Tuple` recursively.