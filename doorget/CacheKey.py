from typing import Tuple


class CacheKey:
    kwargs: Tuple

    def __init__(self, kwargs) -> None:
        self.kwargs = kwargs
    def __eq__(self, another: 'CacheKey') -> bool:
        return hasattr(another, 'kwargs') and self.kwargs == another.kwargs
    def __hash__(self) -> int:
        return hash(self.kwargs)
    def __str__(self) -> str:
        return self.kwargs.__str__()
    def __repr__(self) -> str:
        return self.kwargs.__repr__()
