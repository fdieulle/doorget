from typing import Any, Dict, List
from dataclasses import dataclass

from .CacheKey import CacheKey
from .Storage import Storage


@dataclass
class MemoryStorage(Storage):
    __cache: Dict[CacheKey, Any]

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.__cache = {}

    def contains(self, key: CacheKey) -> bool:
        return key in self.__cache
    def fetch(self, key: CacheKey) -> Any:
        return self.__cache[key]
    def store(self, key: CacheKey, data: Any) -> None:
        self.__cache[key] = data
    
    def clear(self) -> None:
        self.__cache.clear()
    def remove(self, key: CacheKey) -> bool:
        if key in self.__cache:
            del self.__cache[key]
            return True
        return False
    def keys(self) -> List[CacheKey]:
        return self.__cache.keys()
