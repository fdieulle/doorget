from typing import Any, List
from dataclasses import dataclass

from .CacheKey import CacheKey


@dataclass
class Storage:
    name: str

    # Core functions
    def contains(self, key: CacheKey) -> bool:
        """Returns True if the key is stored. False otherwise

        Args:
            key (CacheKey): key

        Returns:
            bool: Returns True if the key is stored. False otherwise
        """
        pass
    def fetch(self, key: CacheKey) -> Any:
        """Fetch the data from the cache.

        When the function is called we assume that the check if key is contains
        has been perfom prior the call.

        Args:
            key (CacheKey): Key

        Returns:
            Any: The cached data
        """
        pass
    def store(self, key: CacheKey, data: Any) -> None:
        """Store a data with its key

        Args:
            key (CacheKey): key
            data (Any): The data to store.
        """
        pass

    # Cache management helpers
    def clear(self) -> None:
        """Clear all cached data.
        """
        pass
    def remove(self, key: CacheKey) -> bool:
        """Remove a cached data by its key

        Args:
            key (CacheKey): key

        Returns:
            bool: Returns True if the data is deleted. False otherwise
        """
        pass
    def keys(self) -> List[CacheKey]:
        """List all the keys contained in the cache

        Returns:
            List[CacheKey]: Return the list of allkeys in the cache
        """
        pass
