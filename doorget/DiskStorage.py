from typing import Any, Dict, List
from dataclasses import dataclass
import pickle
import os
import uuid
import pandas as pd

from .CacheKey import CacheKey
from .Storage import Storage
from .constants import __STORAGES__


__INDEX_DISK_FILE_NAME__ = '__index.bin'


def create_folder(folder: str) -> str:
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def delete_file(file_path: str) -> None:
    if os.path.exists(file_path):
        os.remove(file_path)


def read_pickle(file_path: str, default_value: Any=None) -> Any:
    if not os.path.exists(file_path):
        return default_value
    
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except:
        return default_value


def write_pickle(file_path: str, data: Any) -> Any:
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
    except:
        pass


@dataclass
class DiskStorage(Storage):
    __name: str
    __cache_folder: str
    __index: Dict[CacheKey, str]
    __last_modified_ts: float

    def __init__(self, name: str, cache_folder: str) -> None:
        super().__init__(name)
        self.__name = name
        self.__cache_folder = cache_folder
        self.__last_modified_ts = 0.0
        self.sync_index()

    def get_cache_folder(self) -> str:
        if self.__cache_folder is None:
            return os.path.join(__STORAGES__.disks.default_folder, self.__name)
        return self.__cache_folder
    
    def update_default_folder(self):
        if self.__cache_folder is None:
            self.__last_modified_ts = 0.0
            self.sync_index()
        
    def get_file_path(self, file_name: str) -> str:
        return os.path.join(self.get_cache_folder(), file_name)
    
    def read_pickle(self, file_name: str, default_value: Any=None) -> Any:
        return read_pickle(self.get_file_path(file_name), default_value=default_value)
        
    def write_pickle(self, file_name: str, data: Any) -> Any:
        write_pickle(self.get_file_path(file_name), data)

    def sync_index(self):
        file_path = self.get_file_path(__INDEX_DISK_FILE_NAME__)
        if not os.path.exists(file_path):
            self.__index = {}
            return 
        
        last_modified_ts = os.path.getmtime(file_path)
        if last_modified_ts > self.__last_modified_ts:
            self.__index = self.read_pickle(__INDEX_DISK_FILE_NAME__, default_value={})
            self.__last_modified_ts = last_modified_ts
    
    def update_index(self, key: CacheKey, file_name: str):
        self.sync_index()
        self.__index[key] = file_name
        self.write_pickle(__INDEX_DISK_FILE_NAME__, self.__index)
        self.__last_modified_ts = os.path.getmtime(self.get_file_path(__INDEX_DISK_FILE_NAME__))

    def contains(self, key: CacheKey) -> bool:
        self.sync_index()
        return key in self.__index and os.path.exists(self.get_file_path(self.__index[key]))
    
    def fetch(self, key: CacheKey) -> Any:
        file_name = self.__index[key]
        if file_name.endswith('.pkl'):
            return self.read_pickle(file_name)
        
        try:
            if file_name.endswith('.pqt'):    
                return pd.read_parquet(self.get_file_path())
        except:
            return None
        
    def store(self, key: CacheKey, data: Any) -> None:
        create_folder(self.get_cache_folder())

        if isinstance(data, pd.DataFrame):
            file_name = f'{uuid.uuid4()}.pqt'
            try:
                data.to_parquet(self.get_file_path(file_name))
            except:
                return
        else:
            file_name = f'{uuid.uuid4()}.pkl'
            self.write_pickle(file_name, data)

        self.update_index(key, file_name)
    
    def delete_file(self, key: CacheKey) -> None:
        delete_file(self.get_file_path(self.__index[key]))

    def clear(self) -> None:
        self.sync_index()
        for key in self.__index:
            self.delete_file(key)
        self.__index.clear()

    def remove(self, key: CacheKey) -> bool:
        if key in self.__index:
            self.delete_file(key)
            del self.__index[key]
            return True
        return False
    
    def keys(self) -> List[CacheKey]:
        return self.__index.keys()
