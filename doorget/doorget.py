from typing import Dict

from .Storage import Storage
from .DiskStorage import DiskStorage
from .MemoryStorage import MemoryStorage
from .constants import __STORAGES__


def setup_disk_storage(cache_folder: str):
    __STORAGES__.disks.default_folder = cache_folder


def list_disk_storages() -> Dict[str, DiskStorage]:
    return __STORAGES__.disks.list_storages()


def list_memory_storages() -> Dict[str, MemoryStorage]:
    return __STORAGES__.memories.list_storages()


def list_custom_storages() -> Dict[str, Storage]:
    return __STORAGES__.customs.list_storages()
