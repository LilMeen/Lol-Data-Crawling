import json
from collections import Counter

def normalize_item_name(item_name):
    return item_name.strip().lower()


def build_recipe_map(item_tree):
    recipe_map = {}
    for node in item_tree:
        name = normalize_item_name(node["item"])
        children = [normalize_item_name(child["item"]) for child in node.get("child", [])]
        recipe_map[name] = children
    return recipe_map


def consume_requirements(requirements, inventory):
    hidden_items = []
    for component in requirements:
        if inventory[component] > 0:
            inventory[component] -= 1
            if inventory[component] == 0:
                del inventory[component]
        else:
            hidden_items.append(component)
    return hidden_items



def add_hidden_item_in_build_sequence(item_builds, item_tree):
    item_builds = [normalize_item_name(item) for item in item_builds]
    recipe_map = build_recipe_map(item_tree)
    inventory = Counter()
    full_build = []
    mask = []

    for item in item_builds:
        requirements = recipe_map.get(item, [])
        hidden_build = consume_requirements(requirements, inventory)

        full_build.extend(hidden_build)
        full_build.append(item)

        mask.extend([1] * len(hidden_build))
        mask.append(0)

        inventory[item] += 1


    for item, m in zip(full_build, mask):
        if m == 1:
            print("(",end="")
        print(item, end="")
        if m == 1:
            print(")", end="")
        if item != full_build[-1]:
            print(" -> ", end="")
    return full_build

def remove_unlisted_items(item_builds, item_tree):
    valid_items = set(normalize_item_name(node["item"]) for node in item_tree)
    return [item for item in item_builds if normalize_item_name(item) in valid_items]

def preprocess_item_builds(item_builds, item_tree):
    full_build = add_hidden_item_in_build_sequence(item_builds, item_tree)
    full_build = remove_unlisted_items(full_build, item_tree)
    return full_build