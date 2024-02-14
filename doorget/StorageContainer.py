from typing import Dict, TypeVar, Generic

from .Storage import Storage
from .MemoryStorage import MemoryStorage
from .IdentityStorage import IdentityStorage


T = TypeVar("T")


class StorageContainer(Generic[T]):
    @property
    def registered(self) -> Dict[str, T]:
        return self.__registered
    
    def __init__(self) -> None:
        super().__init__()
        self.__registered: Dict[str, T] = {}
    
    def register(self, name: str, storage: T) -> None:
        self.__registered[name] = storage
    
    def unregister(self, name: str) -> True:
        if name in self.__registered:
            del self.__registered[name]
            return True
        return False
    
    def list_storages(self) -> Dict[str, T]:
        return {name: self.__registered[name] for name in self.__registered}


class DiskStorageContainer(StorageContainer[Storage]):
    @property
    def default_folder(self) -> str:
        return self.__default_folder
    
    @default_folder.setter
    def default_folder(self, value: str) -> None:
        self.__default_folder = value
        for key in self.registered:
            self.registered[key].update_default_folder()
    
    def __init__(self) -> None:
        super().__init__()
        self.__default_folder: str = '.'
    

class Storages:
    @property
    def memories(self) -> StorageContainer[MemoryStorage]:
        return self.__memories
    
    @property
    def disks(self) -> DiskStorageContainer:
        return self.__disks
    
    @property
    def identities(self) -> StorageContainer[IdentityStorage]:
        return self.__identities
    
    @property
    def customs(self) -> StorageContainer[Storage]:
        return self.__customs
    
    def __init__(self) -> None:
        self.__memories : StorageContainer[MemoryStorage] = StorageContainer[MemoryStorage]()
        self.__disks : DiskStorageContainer = DiskStorageContainer()
        self.__identities : DiskStorageContainer[IdentityStorage] = StorageContainer[IdentityStorage]()
        self.__customs : DiskStorageContainer[Storage] = StorageContainer[Storage]()
        