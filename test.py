from preprocessing.preprocess import  preprocess_item_builds
import json

item_tree = json.load(open("item_crawling/items_tree.json", "r", encoding="utf-8"))


example_json = {
    "player": "썸썸데이#KR1Lv.294S15:grandmasterS14-3:diamond2",
    "matchUrl": "https://op.gg/lol/summoners/kr/%25EC%258D%25B8%25EC%258D%25B8%25EB%258D%25B0%25EC%259D%25B4-KR1/matches/ta1XN8oiMOLBQ_Z9Iuyj2oC9NlVymbsRTQItO-wE_jk%3D/1767722502000",
    "type": "Ranked Solo/Duo",
    "time": "3 months ago",
    "result": "Defeat",
    "champion": "viktor",
    "spell": ["Teleport", "Flash"],
    "kda": {
        "kills": 0,
        "deaths": 5,
        "assists": 6
    },
    "kdaRatio": 1.2,
    "position": "Mid",
    "itemBuilds": [
        "Doran's Ring",
        "Health Potion",
        "Stealth Ward",
        "Catalyst of Aeons",
        "Boots",
        "Blasting Wand",
        "Rod of Ages",
        "Fiendish Codex",
        "Blasting Wand",
        "Glowing Mote",
        "Horizon Focus",
        "Control Ward",
        "Sorcerer's Shoes",
        "Control Ward",
        "Amplifying Tome",
        "Seeker's Armguard",
        "Farsight Alteration"
    ]
}

fullbuild = preprocess_item_builds(example_json["itemBuilds"])
print()
print()
for item in fullbuild:
    if item != fullbuild[-1]:
        print(item, end=" -> ")
    else:
        print(item)