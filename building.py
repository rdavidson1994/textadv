import game_object
import location
import name_object
import shopkeeper
import trait
from namemaker import NameMaker, make_name


class Building(location.Location):
    default_name = "building"

    def __init__(self, source_location, *args, replaced_door=None, **kwargs):
        if "name" not in kwargs:
            kwargs["name"] = name_object.Name(self.default_name)
        super().__init__(*args, **kwargs)
        if replaced_door:
            replaced_door.end.name += "(whoops)"
            replaced_door.source.vanish()
            replaced_door.target.vanish()

        self.door = game_object.Door(source_location, self)


class Shop(Building):
    default_name = "shop"
    clerk_title = "shopkeeper"

    def __init__(self, *args, shopkeeper_actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.merchandise = []
        if shopkeeper_actor:
            self.shopkeeper = shopkeeper_actor
        else:
            self.shopkeeper = shopkeeper.Person(
                name=make_name().add(self.clerk_title, "{}, {}"),
                location=self,
            )
            
        self.shopkeeper.shop = self
    
    def become_abandonned(self):
        self.name = self.name + " (abandonned)"
        self.door.source.name += " (abandonned)"


class Temple(Shop):
    default_name = "temple"
    clerk_title = "monk"


class Inn(Shop):
    default_name = "inn"
    clerk_title = "innkeeper"

    def __init__(self, *args, room_price=5, **kwargs):
        super().__init__(*args, **kwargs)
        self.traits.add(trait.inn())
        self.room_price = room_price


class WeaponShop(Shop):
    default_name = "weapon shop"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shopkeeper.money = 2000

        sword = game_object.Item(name="spear", location=self)
        sword.price = 100
        sword.damage_mult = 6
        sword.damage_type = "sharp"
        sword.owner = self.shopkeeper

        armor = game_object.Item(name="armor", location=self)
        armor.price = 150
        armor.traits.add(trait.armor())
        armor.damage_reduction = 2
        armor.owner = self.shopkeeper
