from discord import Colour


def get_color_by_class_name(class_name):
    switcher = {
        "death knight": Colour.from_rgb(196, 30, 59),
        "demon hunter": Colour.from_rgb(163, 48, 201),
        "druid": Colour.from_rgb(255, 125, 10),
        "hunter": Colour.from_rgb(171, 212, 115),
        "mage": Colour.from_rgb(105, 204, 240),
        "monk": Colour.from_rgb(0, 255, 150),
        "paladin": Colour.from_rgb(245, 140, 186),
        "priest": Colour.from_rgb(255, 255, 255),
        "rogue": Colour.from_rgb(255, 245, 105),
        "shaman": Colour.from_rgb(0, 112, 222),
        "warlock": Colour.from_rgb(148, 130, 201),
        "warrior": Colour.from_rgb(199, 156, 110)
    }
    class_name = class_name.lower()
    return switcher.get(class_name, Colour.from_rgb(255, 255, 255))

def get_class_icon(class_name):
    switcher = {
        "death knight": "https://gamepedia.cursecdn.com/wowpedia/e/e5/Ui-charactercreate-classes_deathknight.png",
        "demon hunter": "https://gamepedia.cursecdn.com/wowpedia/c/c9/Ui-charactercreate-classes_demonhunter.png",
        "druid": "https://gamepedia.cursecdn.com/wowpedia/6/6f/Ui-charactercreate-classes_druid.png",
        "hunter": "https://gamepedia.cursecdn.com/wowpedia/4/4e/Ui-charactercreate-classes_hunter.png",
        "mage": "https://gamepedia.cursecdn.com/wowpedia/5/56/Ui-charactercreate-classes_mage.png",
        "monk": "https://gamepedia.cursecdn.com/wowpedia/2/24/Ui-charactercreate-classes_monk.png",
        "paladin": "https://gamepedia.cursecdn.com/wowpedia/8/80/Ui-charactercreate-classes_paladin.png",
        "priest": "https://gamepedia.cursecdn.com/wowpedia/0/0f/Ui-charactercreate-classes_priest.png",
        "rogue": "https://gamepedia.cursecdn.com/wowpedia/b/b1/Ui-charactercreate-classes_rogue.png",
        "shaman": "https://gamepedia.cursecdn.com/wowpedia/3/3e/Ui-charactercreate-classes_shaman.png",
        "warlock": "https://gamepedia.cursecdn.com/wowpedia/c/cf/Ui-charactercreate-classes_warlock.png",
        "warrior": "https://gamepedia.cursecdn.com/wowpedia/3/37/Ui-charactercreate-classes_warrior.png"
    }
    class_name = class_name.lower()
    return switcher.get(class_name, None)