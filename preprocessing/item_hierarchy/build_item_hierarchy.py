from __future__ import annotations

import json

from preprocessing.config.constants import (
    ITEM_SOURCE_PATH,
    PREPROCESS_DATA_DIR,
    PREPROCESS_ITEM_TREE_PATH,
    PREPROCESS_REMOVED_ITEMS_PATH,
)
from preprocessing.item_hierarchy.all_delete_item import fetch_removed_items


EXCLUDED_CATEGORIES = {"Consumable", "Trinket"}


def load_items() -> list[dict]:
    with open(ITEM_SOURCE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_removed_names() -> set[str]:
    with open(PREPROCESS_REMOVED_ITEMS_PATH, "r", encoding="utf-8") as f:
        names = json.load(f)
    return {(name or "").strip().lower() for name in names}


def has_excluded_category(item: dict) -> bool:
    categories = item.get("categories", []) or []
    return any(category in EXCLUDED_CATEGORIES for category in categories)


def build_canonical_maps(items: list[dict], removed_names: set[str]) -> tuple[dict[str, dict], dict[int, dict]]:
    filtered_items: list[dict] = []
    for item in items:
        if has_excluded_category(item):
            continue

        lower_name = (item.get("name") or "").strip().lower()
        if not lower_name:
            continue

        if lower_name in removed_names:
            continue

        filtered_items.append(item)

    canonical_by_name: dict[str, dict] = {}
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

    id_to_canonical: dict[int, dict] = {}
    for item_id, item in id_to_item.items():
        lower_name = (item.get("name") or "").strip().lower()
        canonical = canonical_by_name.get(lower_name)
        if canonical:
            id_to_canonical[item_id] = canonical

    return canonical_by_name, id_to_canonical


def build_tree(item: dict, id_to_canonical: dict[int, dict], cache: dict[int, dict], visiting: set[int]) -> dict:
    item_id = item.get("id")
    if item_id in cache:
        return cache[item_id]

    if item_id in visiting:
        return {"item": (item.get("name") or "").strip().lower()}

    visiting.add(item_id)

    children: list[dict] = []
    for child_id in item.get("from", []) or []:
        canonical_child = id_to_canonical.get(child_id)
        if not canonical_child:
            continue
        child_tree = build_tree(canonical_child, id_to_canonical, cache, visiting)
        if child_tree is not None:
            children.append(child_tree)

    tree = {"item": (item.get("name") or "").strip().lower()}
    if children:
        tree["child"] = children
    cache[item_id] = tree
    visiting.remove(item_id)
    return tree


def build_item_hierarchy() -> None:
    PREPROCESS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PREPROCESS_REMOVED_ITEMS_PATH.exists():
        print(f"{PREPROCESS_REMOVED_ITEMS_PATH} not found. Fetching removed items from wiki...")
        fetch_removed_items()
    removed_names = load_removed_names()

    items = load_items()
    canonical_by_name, id_to_canonical = build_canonical_maps(items, removed_names)

    cache: dict[int, dict] = {}
    result: list[dict] = []
    for canonical_item in canonical_by_name.values():
        tree = build_tree(canonical_item, id_to_canonical, cache, set())
        if tree is not None:
            result.append(tree)

    with open(PREPROCESS_ITEM_TREE_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
