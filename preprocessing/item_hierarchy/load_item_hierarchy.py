
import json

from preprocessing.config.constants import PREPROCESS_ITEM_TREE_PATH
from preprocessing.item_hierarchy.build_item_hierarchy import build_item_hierarchy


def load_item_tree(item_tree_path: str = str(PREPROCESS_ITEM_TREE_PATH)) -> list[dict]:
    if not PREPROCESS_ITEM_TREE_PATH.exists() and item_tree_path == str(PREPROCESS_ITEM_TREE_PATH):
        build_item_hierarchy()

    with open(item_tree_path, "r", encoding="utf-8") as f:
        item_tree = json.load(f)
    return item_tree
