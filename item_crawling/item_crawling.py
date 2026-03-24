import json
from pathlib import Path

INPUT_PATH = Path(__file__).with_name("item.json")
OUTPUT_PATH = Path(__file__).with_name("items_tree.json")
REMOVED_ITEMS_PATH = Path(__file__).with_name("removed_items.json")
EXCLUDED_CATEGORIES = {"Consumable", "Trinket"}


def load_items():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_removed_names():
    with open(REMOVED_ITEMS_PATH, "r", encoding="utf-8") as f:
        names = json.load(f)
    return {(name or "").strip().lower() for name in names}


def has_excluded_category(item):
    categories = item.get("categories", []) or []
    return any(category in EXCLUDED_CATEGORIES for category in categories)


def build_canonical_maps(items, removed_names):
    filtered_items = []
    for item in items:
        if has_excluded_category(item):
            continue

        lower_name = (item.get("name") or "").strip().lower()
        if not lower_name:
            continue

        if lower_name in removed_names:
            continue

        filtered_items.append(item)

    # Keep one canonical item per lowercase name.
    # If duplicates exist, prefer the one that has recipe components in "from".
    canonical_by_name = {}
    for item in filtered_items:
        lower_name = (item.get("name") or "").strip().lower()
        if not lower_name:
            continue
        if lower_name not in canonical_by_name:
            canonical_by_name[lower_name] = item
            continue

        current = canonical_by_name[lower_name]
        current_has_from = bool(current.get("from"))
        incoming_has_from = bool(item.get("from"))

        if incoming_has_from and not current_has_from:
            canonical_by_name[lower_name] = item

    id_to_item = {item.get("id"): item for item in filtered_items if item.get("id") is not None}

    # Map every id to its canonical item (first occurrence of that lowercase name).
    id_to_canonical = {}
    for item_id, item in id_to_item.items():
        lower_name = (item.get("name") or "").strip().lower()
        canonical = canonical_by_name.get(lower_name)
        if canonical:
            id_to_canonical[item_id] = canonical

    return canonical_by_name, id_to_canonical


def build_tree(item, id_to_canonical, cache, visiting):
    item_id = item.get("id")
    if item_id in cache:
        return cache[item_id]

    if item_id in visiting:
        return {"item": (item.get("name") or "").strip().lower()}

    visiting.add(item_id)

    children = []
    seen_child_names = set()
    for child_id in item.get("from", []) or []:
        canonical_child = id_to_canonical.get(child_id)
        if not canonical_child:
            continue
        child_tree = build_tree(canonical_child, id_to_canonical, cache, visiting)
        if child_tree is not None and child_tree["item"] not in seen_child_names:
            children.append(child_tree)
            seen_child_names.add(child_tree["item"])

    tree = {"item": (item.get("name") or "").strip().lower()}
    if children:
        tree["child"] = children
    cache[item_id] = tree
    visiting.remove(item_id)
    return tree


def main():
    items = load_items()
    removed_names = load_removed_names()
    canonical_by_name, id_to_canonical = build_canonical_maps(items, removed_names)

    cache = {}
    result = []
    for canonical_item in canonical_by_name.values():
        tree = build_tree(canonical_item, id_to_canonical, cache, set())
        if tree is not None:
            result.append(tree)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Built {len(result)} unique item recipe trees")
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()


