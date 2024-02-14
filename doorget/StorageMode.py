from enum import Enum


class StorageMode(str, Enum):
    Memory = 'Memory'
    Disk = 'Disk'
    Identity = 'Identity' # TODO: Link a better name ?
    Custom = 'Custom'

    def __repr__(self) -> str:
        return self.name
    def __str__(self) -> str:
        return self.name
