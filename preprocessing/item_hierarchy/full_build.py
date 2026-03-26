from collections import Counter

def normalize_item_name(item_name: str) -> str:
    return item_name.strip().lower()


def build_recipe_map(item_tree: list[dict]) -> dict[str, list[str]]:
    recipe_map: dict[str, list[str]] = {}
    for node in item_tree:
        name = normalize_item_name(node["item"])
        children = [normalize_item_name(child["item"]) for child in node.get("child", [])]
        recipe_map[name] = children
    return recipe_map


def consume_requirements(requirements: list[str], inventory: Counter) -> list[str]:
    hidden_items: list[str] = []
    for component in requirements:
        if inventory[component] > 0:
            inventory[component] -= 1
            if inventory[component] == 0:
                del inventory[component]
        else:
            hidden_items.append(component)
    return hidden_items


def add_hidden_item_in_build_sequence(item_builds: list[str], item_tree: list[dict]) -> list[str]:
    item_builds = [normalize_item_name(item) for item in item_builds]
    recipe_map = build_recipe_map(item_tree)
    inventory: Counter = Counter()
    full_build: list[str] = []

    for item in item_builds:
        requirements = recipe_map.get(item, [])
        hidden_build = consume_requirements(requirements, inventory)
        full_build.extend(hidden_build)
        full_build.append(item)
        inventory[item] += 1

    return full_build


def remove_unlisted_items(item_builds: list[str], item_tree: list[dict]) -> list[str]:
    valid_items = {normalize_item_name(node["item"]) for node in item_tree}
    return [item for item in item_builds if normalize_item_name(item) in valid_items]


def create_full_build(item_builds: list[str], item_tree: list[dict]) -> list[str]:
    full_build = add_hidden_item_in_build_sequence(item_builds, item_tree)
    full_build = remove_unlisted_items(full_build, item_tree)
    return full_build
