from typing import Type, TypeVar, Optional
from dataclasses import dataclass
from copy import copy

class TraitSet:
    def __init__(self):
        self.components = {}
    
    T = TypeVar('T')
    def __getitem__(self, key: Type[T]) -> Optional[T]:
        return self.components.get(key, None)
    
    def __setitem__(self, key: Type[T], val: T):
        self.components[key] = copy(val)
    
    def contains_trait(self, key: Type[T]):
        return key in self.components
    
    def add(self, new_trait):
        self.components[type(new_trait)] = copy(new_trait)

@dataclass
class item: pass

@dataclass
class food: pass

@dataclass
class container: pass

@dataclass
class lockable: pass

@dataclass
class portal: pass

@dataclass
class location: pass

@dataclass
class inn: pass

@dataclass
class actor: pass

@dataclass
class wide: pass

@dataclass
class listener: pass

@dataclass
class town: pass

@dataclass
class person: pass

@dataclass
class merchant: pass

@dataclass
class hero: pass

@dataclass
class interesting: pass

@dataclass
class readable: pass

@dataclass
class meat: pass

@dataclass
class kobold: pass

@dataclass
class armor: pass

@dataclass
class corpse: pass