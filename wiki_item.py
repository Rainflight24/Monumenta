"""
This interactive script generates a wikipage for a Monumenta item.

It does NOT generate:
- Obtaining
- Any extra information not included in the api

(Charms are not supported by the wiki.)

The generated location and enchant order may be incorrect.
"""

from __future__ import annotations
import os
import re
import requests

# Config:
CLIPBOARD = False  # Whether to copy the most recent item using pyperclip.
MAX_FILES = 10  # Save up to MAX_FILES files. Set to 0 for None.
PREFIX = "output" + "/"  # Folder to save files to.
HIDE_OUTPUT = False  # Disables outputting the resulting item page.

if CLIPBOARD:
    print("Importing pyperclip...")
    import pyperclip


class Item:
    """
    Represents an Item from the Monumenta API.
    """
    # Maps api location names to their wiki name.  Lowercase only.
    locMap = {
        # Direct mappings.
        "april's fools": "aprilfools",
        "Special Artist Plushie - Collect Them All! is not in the api": None,
        "azacor": "azacor",
        "blitz": "blitz",
        "blue": "blue",
        "brown": "brown",
        "carnival": "carnival",
        "valley casino": "casino1",
        "isles casino": "casino2",
        "ring casino": "casino3",
        "cyan": "cyan",
        "delves": "delves",
        "divine skin": "divine",
        "docks": "docks",
        "easter": "easter",
        "corridors": "ephemeral",
        "ephemeral enhancements": "ephemeralenhancements",
        "forum": "forum",
        # This should really be changed in the wiki.
        "eldrask": "the waking giant",
        "gray": "gray",
        "greed skin": "greedskin",
        "halloween event": "halloween",
        "halloween skin": "halloween skin",
        "the hoard": "hoard",
        "holiday skin": "holidayskin",
        "horseman": "horseman",
        "intellect crystallizer": "intellect",
        "kaul": "kaul",
        "labs": "labs",
        "hekawt": "lich",  # This should really be changed in the wiki.
        # This should really be changed in the wiki.
        "arena of terth": "light",
        "light blue": "lightblue",
        "light gray": "lightgray",
        "lime": "lime",
        "lowtide smuggler": "lowtide smuggler",
        "magenta": "magenta",
        "mist": "mist",
        "mythic reliquary": "mythic",
        "orange": "orange",
        "valley overworld": "overworld1",
        "isles overworld": "overworld2",
        "pelias' keep": "pelias",
        "pink": "pink",
        "portal": "portal",
        "purple": "purple",
        "quest reward": "quest",
        "remorse": "remorse",
        "remorseful skin": "remorsefulskin",
        "reverie": "reverie",
        "royal armory": "royal",
        "ruin": "ruin",
        "rush": "rush",
        "sanctum": "sanctum",
        "sanguine halls": "sanguine",
        "seasonal pass": "seasonpass",
        "shifting": "shifting",
        "skt": "silverknightstomb",
        "soulwoven": "soul",
        "teal": "teal",
        "titanic skin": "titanicskin",
        "transmogifier": "transmogifier",
        "tov": "treasure",
        "trickster": "trickster",  # Legacy. Probably won't see any use.
        "uganda": "uganda",
        "valentine's day": "valentine",
        "verdant": "verdant",
        "threadwarped skin":
        "verdantskin",  # This should maybe be changed on the wiki?
        "the eternal vigil": "vigil",
        "white": "white",
        "willows": "willows",
        "storied skin":
        "willowskin",  # This should maybe be changed on the wiki?
        "winter event": "winter",
        "the wolfswood": "wolfswood",
        "yellow": "yellow",

        # Mappings to "".
        "king's valley": "",
        "celsian isles": "",
        "architect's ring": ""
    }

    # Maps item types to their respective slot.
    slotMap = {
        "mainhand": "mainhand",
        "wand": "mainhand",
        "scythe": "mainhand",
        "pickaxe": "mainhand",
        "shovel": "mainhand",
        "axe": "mainhand",
        "trident": "mainhand",
        "snowball": "mainhand",
        "stick": "mainhand",
        "bow": "mainhand",
        "crossbow": "mainhand",
        "consumable": "",
        "fishing rod": "mainhand",
        "mainhand sword": "mainhand",
        "offhand sword": "offhand",
        "mainhand shield": "mainhand",
        "offhand shield": "offhand",
        "offhand": "offhand",
        "misc": "",
        "helmet": "helmet",
        "chestplate": "chest",
        "leggings": "legs",
        "boots": "feet",
        "charm": "charm"
    }

    # Maps attributes attributes between the api and wiki.
    attributes = {
        # Defensive Attributes.
        "max_health_flat": "Max Health Add",
        "max_health_percent": "Max Health Multiply",
        "agility": "Agility",
        "agility_percent": "Agility Multiply",
        "armor": "Armor",
        "armor_percent": "Armor Multiply",

        # Offensive Attributes.
        "attack_damage_base": "Attack Damage Add",
        "attack_damage_percent": "Attack Damage Multiply",
        "attack_speed_base": "Attack Speed Add",
        "attack_speed_flat": "Attack Speed Add",
        "attack_speed_percent": "Attack Speed Multiply",
        "spell_power_base": "Spell Power",
        "magic_damage_percent": "Magic Power Multiply",
        "projectile_damage_base": "Projectile Damage Add",
        "projectile_damage_percent": "Projectile Damage Multiply",
        "projectile_speed_base": "Projectile Speed Add",
        "projectile_speed_percent": "Projectile Speed Multiply",
        "throw_rate_base": "Throw Rate",
        "throw_rate_percent": "Throw Rate Multiply",
        "potion_radius_flat": "Potion Radius",
        "potion_damage_flat": "Potion Damage",

        # Misc.
        "knockback_resistance_flat": "Knockback Resistance",
        "speed_flat": "Speed Add",
        "speed_percent": "Speed Multiply",
        "thorns_flat": "Thorns Damage"
    }
    """A class representing a Monumenta item."""

    def __init__(self, raw_json: dict):
        self.name = raw_json["name"] if "name" in raw_json else None
        self.type = raw_json["base_item"] if "base_item" in raw_json else None
        try:
            self.slot = Item.slotMap[
                raw_json["type"].lower()] if "type" in raw_json else None
        except KeyError:
            print("No slot found!", self.name, raw_json)
            self.slot = ""
        self.slot2 = ""

        self.region = raw_json["region"] if "region" in raw_json else None
        self.tier = raw_json["tier"] if "tier" in raw_json else None
        self.charm_power = raw_json["power"] if "power" in raw_json else None
        self.charm_class = raw_json[
            "class_name"] if "class_name" in raw_json else None
        self.formatted_loc = raw_json[
            "location"] if "location" in raw_json else None
        self.loc = Item.locMap[self.formatted_loc.lower(
        )] if self.formatted_loc and self.formatted_loc.lower(
        ) in Item.locMap else ""

        # All charm stats are attributes.
        if self.slot == "charm":
            self.enchantments = {}
            self.attributes = raw_json["stats"] if "stats" in raw_json else None
        else:
            self.enchantments = {
                name: value
                for name, value in raw_json["stats"].items()
                # Non-attribute stats are enchantments.
                if name not in Item.attributes
            } if "stats" in raw_json else None
            self.attributes = {
                name: value
                for name, value in raw_json["stats"].items()
                if name in Item.attributes
            } if "stats" in raw_json else None

        self.lore = raw_json["lore"].replace(
            "\n", " ") if "lore" in raw_json else None

        self.masterwork = int(
            raw_json["masterwork"]) if "masterwork" in raw_json else None
        self.masterwork_data = {}

    def __str__(self) -> str:
        return f"{self.name} ({Item.mw_stars(self.masterwork)})"

    def __lt__(self, other: Item) -> bool:
        mw1 = self.masterwork if self.masterwork else -1
        mw2 = other.masterwork if other.masterwork else -1

        if mw1 == mw2:
            return self.name < other.name

        return mw1 < mw2

    @staticmethod
    def format_stat(string: str, remove: tuple[str] = None) -> str:
        """
        Replaces underscores and capitalizes a stat to format it.

        Removes all instances of strings in remove.
        """
        string = string.lower()

        # Insensitively remove all strings in remove.
        if remove:
            for to_remove in remove:
                string = string.replace(to_remove.lower(), "")

        # Capitalize each word. Remove underscores.
        string = string.replace("_", " ").split()
        string = [word.capitalize() for word in string]
        return ' '.join(string)

    @staticmethod
    def format_list(pairs: dict[any, any],
                    template: str,
                    key_dict: dict = None) -> str:
        """
        Converts a list of key, value pairs into template.

        Returns a string representation of this, one newline per entry.
        Each entry: {{Template|str|int}}
        """
        string = ""
        for key, value in pairs.items():
            string += ("{{" + template + "|" + Item.format_stat(
                str(key_dict[key] if key_dict and key in key_dict else key)) +
                "|" + str(value / 100 if "percent" in key or "power" in
                          key else value) +
                ("|true" if "base" in key else "") + "}}\n")
        return string[:-1]  # Trim trailing newline.

    def add_mw(self, other: Item):
        """Appends masterwork data to this item."""
        if other.masterwork is not None:
            self.masterwork_data[other.masterwork] = other

    @staticmethod
    def mw_stars(cur: int, limit: int = None) -> str:
        """Generates masterwork stars."""
        if limit is None:
            limit = cur
        star_filled = "★"
        star_empty = "☆"
        return star_filled * cur + star_empty * (limit - cur)

    def to_wiki(self) -> str:
        """Converts an Item to a Template:Item."""
        # Maps Template:Item parameters to api paramenters.
        param_dict = {
            "name": self.name,
            "image": "",
            "type": self.type,
            "slot": self.slot,
            "slot2": self.slot2,
            "region": self.region,
            "tier": self.tier,
            "location": self.loc,
            "enchantments": Item.format_list(self.enchantments, "Item/Enchantment"),
            "attributes": "{{Item/AttributeGroup|" + self.slot + "}}\n" +
            Item.format_list(self.attributes, "Item/Attribute",
                             Item.attributes) if self.slot else "",
            "charm_power": self.charm_power,
            "charm_class": self.charm_class,
        }

        # Item template usage.
        string = "{{Item\n"

        for param, value in param_dict.items():
            string += f"|{param}="
            if value is not None:
                string += str(value)
            string += "\n"

        # Article main body.
        string += (
            "}}\n"
            + "{{WorkInProgress|Autogenerated stub. Missing:\n"
            + "*Obtaining\n"
            + "*More details (if possible)\n"
            + "*Double check autogenerated text\n"
            + "*Double check enchant/attribute order\n"
            + "*Categories\n"
            + "}}\n"
            + "{{PAGENAME}}" + f" is a {self.tier if not None else ''}"
            + f" {self.type if self.type else ''} found inside "
            + f"[[{self.formatted_loc if self.formatted_loc else ''}]].\n"
            + (("== Lore ==\n" + "''\"" + self.lore +
                "\"''\n") if self.lore else "") + "== Obtaining ==\n")

        # Article masterworking section, if neccessary.
        if self.masterwork_data:
            # Get the highest masterwork level.
            max_mw = -1
            max_item = None
            for masterwork, item in self.masterwork_data.items():
                if masterwork > max_mw:
                    max_mw = masterwork
                    max_item = item

            # Generate an ordered list of stats from max_item.
            stats = max_item.attributes | max_item.enchantments

            string += ("== Masterworking ==\n" + '{|class="article-table"\n' +
                       "!'''Masterwork Level'''\n")
            for stat in stats:
                stat = Item.format_stat(stat, ("percent", "base", "flat"))
                string += f"!'''{stat}'''\n"
            string += "|-\n"

            # Fill the table with each masterwork level.
            for masterwork, item in self.masterwork_data.items():
                item_stats = item.attributes | item.enchantments
                string += f"|{Item.mw_stars(masterwork, max_mw)}\n"
                for stat in stats:
                    string += f"|{item_stats[stat] if stat in item_stats else ''}"
                    if "percent" in stat:
                        string += "%"
                    string += '\n'

                string += "|-\n"

            string += "|}\n"

        string += "{{ItemNavbox}}\n"

        # Categories are not implemented.
        string += "[[Category:NotImplemented]]\n"

        return string


class ItemAPI:
    """
    Accesses and processes data from the Monumenta item api.
    """
    s = requests.Session()

    def __init__(self):
        resp = ItemAPI.s.get("https://api.playmonumenta.com/items")
        self.items = resp.json()
        resp.close()

    def reload(self):
        """Reload this object's version of the database."""
        resp = ItemAPI.s.get("https://api.playmonumenta.com/items")
        self.items = resp.json()
        resp.close()

    def get(self, item: str) -> list[Item]:
        """
        Return the queried item's json.

        Returns a list of all matching items, or [].
        """
        matches = []
        item = item.lower()
        for item_name, item_json in self.items.items():
            if item_name.lower().startswith(item):
                matches.append(Item(item_json))

        return matches


def main():
    """User input function for wiki_item.py."""
    api = ItemAPI()

    query = ""
    while "quit" not in query:
        query = input("Enter an item, or quit: ")
        items = api.get(query)

        if "quit" in query:
            continue

        if items:
            # Parse for the name(s) of items, without masterwork.
            item_names = set(
                re.match(r".+(?=-\d)|.+", item.name).group() for item in items)

            # Sort the array of items by masterwork.
            items = sorted(items)

            # Fill masterwork data.
            if len(item_names) == 1:
                for item in items:
                    items[0].add_mw(item)
                # Remove masterwork item duplicates.
                items = [items[0]]

            else:
                print("Multiple items found; outputting the first 10:")

            for item in items[:10]:
                if not HIDE_OUTPUT:
                    print(item.to_wiki())

            # Create FOLDER if neccessary.
            if PREFIX:
                try:
                    os.mkdir(PREFIX)
                    print("Created folder", PREFIX)
                except FileExistsError:
                    pass
                except FileNotFoundError as err:
                    print(f"Folder {PREFIX} was not created:", err.strerror)

            # Write the first MAX_FILES files to PREFIX item name.
            for i in range(min(len(items), MAX_FILES)):
                print(f"Writing file {PREFIX}{items[i].name}...")

                try:
                    with open(PREFIX + items[i].name, "w",
                              encoding="utf-8") as file:
                        file.write(items[i].to_wiki())
                except OSError as err:
                    print("Invalid file name!",
                          f"{PREFIX}{items[i].name} was not created.",
                          f"Error: {err.strerror}")

            # Copy the most recently outputted item.
            if CLIPBOARD:
                print(f"Copying {item.name} to clipboard...")
                pyperclip.copy(item.to_wiki())

        else:
            print("Item not found.")


if __name__ == "__main__":
    main()
