from typing import Type, TypeVar, Optional
from copy import copy

class TraitSet:
    def __init__(self):
        self.components = {}
    
    T = TypeVar('T')
    def __getitem__(self, key: Type[T]) -> Optional[T]:
        return self.components.get(key, None)
    
    def __setitem__(self, key, val):
        self.components[key] = copy(val)