import game_object
import location
import name_object
import shopkeeper
from namemaker import NameMaker, make_name


class Building(location.Location):
    def __init__(self, source_location, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.door = game_object.Door(source_location, self)


class Shop(Building):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shopkeeper = shopkeeper.Person(
            name=make_name().add("shopkeeper", "{}, {}"),
            location=self
        )


class WeaponShop(Shop):
    def __init__(self, *args, **kwargs):
        if "name" not in kwargs:
            kwargs["name"] = name_object.Name("weapon shop")
        super().__init__(*args, **kwargs)
        self.shopkeeper.money = 2000

        sword = game_object.Item(name="spear", location=self)
        sword.price = 100
        sword.damage_mult = 6
        sword.damage_type = "sharp"
        sword.owner = self.shopkeeper

        armor = game_object.Item(name="armor", location=self)
        armor.price = 150
        armor.owner = self.shopkeeper

def town_at_point():
    pass