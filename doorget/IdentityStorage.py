from typing import Any, List
from dataclasses import dataclass

from .CacheKey import CacheKey
from .Storage import Storage


@dataclass
class IdentityStorage(Storage):
    def contains(self, key: CacheKey) -> bool:
        return False  # always call the memoized function

    def fetch(self, key: CacheKey) -> Any:
        raise Exception("The identity storage shouldn't use that function")

    def store(self, key: CacheKey, data: Any) -> None:
        pass  # do nothing

    def clear(self) -> None:
        pass  # do nothing

    def remove(self, key: CacheKey) -> bool:
        return False  # untrackable

    def keys(self) -> List[CacheKey]:
        pass  # untrackable
