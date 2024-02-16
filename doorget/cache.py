from typing import Any, Callable, Tuple
import functools
from inspect import signature, Signature, Parameter

from .StorageMode import StorageMode
from .Storage import Storage
from .MemoryStorage import MemoryStorage
from .DiskStorage import DiskStorage
from .IdentityStorage import IdentityStorage
from .CacheKey import CacheKey
from .constants import __STORAGES__


def __unlist(x: Any) -> Tuple:
    if isinstance(x, list):
        return tuple((__unlist(x_i) for x_i in x))
    if isinstance(x, dict):
        return tuple(((__unlist(k), __unlist(v)) for k, v in x.items()))
    return x


def __get_key(signature: Signature, *args, **kwargs) -> CacheKey:
    # fill all parameters by keeping order
    order = {}
    for name in signature.parameters:
        p = signature.parameters[name]
        order[name] = p.default if p.default != Parameter.empty else None

    # update key-values
    order.update(**kwargs)
    # update by filling with positionals
    free_pars = (k for k, _ in order.items())
    order.update(zip(free_pars, args))

    # substitute dependent data with key
    for k, v in order.items():
        if id(v) in __REFS_CACHE__:
            order[k] = __REFS_CACHE__[id(v)]
        else:
            order[k] = __unlist(v)

    return CacheKey(tuple(order.items()))


def __create_storage(
    mode: StorageMode, func: Callable, cache_folder: str, custom_storage: Storage
) -> Storage:
    name = f"{func.__module__}.{func.__name__}"

    if mode == StorageMode.Disk or cache_folder is not None:
        storage = DiskStorage(name=name, cache_folder=cache_folder)
        __STORAGES__.disks.register(name, storage)
        return storage

    if mode == StorageMode.Custom or custom_storage is not None:
        if storage is None or isinstance(storage, Storage):
            raise (f"Custom storage {storage} should inherit from Storage")
        __STORAGES__.customs.register(name, storage)
        return storage

    if mode == StorageMode.Identity:
        storage = IdentityStorage(name=name)
        __STORAGES__.identities.register(name, storage)
        return storage

    if mode == StorageMode.Memory:
        storage = MemoryStorage(name=name)
        __STORAGES__.memories.register(name, storage)
        return storage

    raise Exception(f"Storage mode: {mode} is not supported")


__REFS_CACHE__ = {}


def __memorize_identity(key: CacheKey, data: Any) -> None:
    __REFS_CACHE__[id(data)] = key

    if isinstance(data, tuple):  # Handle multiple returns
        for x in data:
            __REFS_CACHE__[id(x)] = key


def cache(
    func: Callable = None,
    *,
    mode: StorageMode = StorageMode.Memory,
    cache_folder: str = None,
    readonly: bool = False,
    custom_storage: Storage = None,
):
    """Memoize a function

    Memoize a function by choosing which storage mode you would like to use. In memory by default.
    This memoization decorator proposes natively to track and support function dependencies through all
    memoized function no matter which storage is used to.

    * **Memory**: Stores the date in memory. This mode can lead memory leak if it's too much use for large data.
    * **Disk**: Stores the returned data into a file. This mode is usefull for interprocess usage. You can specify
        a custom `cache_folder` or use the default one. The default cache folder is defined through the function
        `setup_disk_storage`. The default cache folder can be changed at any time on the fly.
        If a custom `cache_folder` is defined it cannot be changed at runtime. If you specify only the `cache_folder`
        parameter, the `Disk` mode will be used atomatically.
    * **Identity**: Stores the object memory address only. Sometimes a transformation on your data is faster to be ran than
        loaded from any storage. In this case you want to preserve your function dependencies without store anything.
        In addition it has a low touch in memory.

        To give you a concrete example:
        ```
        >>> @cache
        >>> def f1(id: int) -> pd.DataFrame:
        >>>     pass # Long run

        >>> @cache(mode=StorageMode.Identity)
        >>> def transform(df: pd.DataFrame) -> pd.DataFrame:
        >>>     return df.copy() # or any other transformations like outliers filtering, groupy/agg ... which can swaps the original data to a new object.

        >>> @cache
        >>> def f2(df: pd.DataFrame, name: str) -> pd.DataFrame:
        >>>     pass # Long run

        >>> df = f1(10) # Key = f1_(10)
        >>> df2 = transform(df1) # Key = transform_(f1_(10))
        >>> r = f2(df2, "foo") # Key = f2_(transform_(f1_(10)), foo)
        ```
    * **Custom** Specify your own storage by providing an implementation of the `Storage` class through the `custom_storage` parameter.
        If you specify only the `custom_storage` parameter, the `Custom` mode will be apply atomatically.

    Args:
        func (Callable, optional): Function which will be decorated. Defaults to None.
        mode (StorageMode, optional): Storage mode. Defaults to StorageMode.Default.
        cache_folder (str, optional): Cache folder override. If specified with the `Disk`
            storage mode the cache folder used will override the default one specified
            through `setup_disk_storage` function. None means no override. Defaults to None.
        readonly (bool, optional): Specify if the memoization is readonly. Defaults to False.
        custom_storage (Storage, optional): Define a custome storage. Defaults to None.
    """

    def decorate_cache(_func: Callable):
        @functools.wraps(_func)
        def wrap_cache(*args, **kwargs) -> Any:

            key = __get_key(wrap_cache.signature, *args, **kwargs)
            if wrap_cache.storage.contains(key):
                result = wrap_cache.storage.fetch(key)
            else:
                result = _func(*args, **kwargs)
                if not readonly:
                    wrap_cache.storage.store(key, result)

            # Handle dependencies
            __memorize_identity(key, result)

            return result

        wrap_cache.signature = signature(_func)
        wrap_cache.storage = __create_storage(mode, _func, cache_folder, custom_storage)

        return wrap_cache

    if func is None:
        return decorate_cache
    else:
        return decorate_cache(func)
