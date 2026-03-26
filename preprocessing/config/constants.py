from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
PREPROCESS_DATA_DIR = ROOT_DIR / "data" / "preprocess"

# Source item metadata still comes from the scraped static item file.
ITEM_SOURCE_PATH = ROOT_DIR / "preprocessing" / "config" / "item.json"

PREPROCESSED_MATCHES_PATH = PREPROCESS_DATA_DIR / "matches_preprocessed.parquet"
PREPROCESS_ITEM_TREE_PATH = PREPROCESS_DATA_DIR / "items_tree.json"
PREPROCESS_REMOVED_ITEMS_PATH = PREPROCESS_DATA_DIR / "removed_items.json"

WIKI_ITEMS_URL = "https://wiki.leagueoflegends.com/en-us/List_of_items"
TARGET_SECTIONS = [
    "Removed items",
    "Arena exclusive items",
    "Arena Anvil items",
    "Arena Prismatic items",
    "Minion and Turret items",
    "Champion exclusive items",
]
