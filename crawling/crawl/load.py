import requests
from typing import Any


# ====================================
# FETCH ITEM, SPELL DATA FROM DDRAGON
# ====================================
# 
# load_ddragon_maps
#   Parameters:
#       - version: Optional version string (e.g., "13.12.1"). If None, uses the latest version.
#   Returns:
#       - item_map: A dictionary mapping item IDs to their names.
#       - spell_map: A dictionary mapping spell IDs to their names.
# ====================================
def _fetch_ddragon_json(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


def load_ddragon_maps(version: str = None) -> tuple[dict[int, str], dict[int, str]]:
    versions = _fetch_ddragon_json("https://ddragon.leagueoflegends.com/api/versions.json")
    latest = version if version is not None else versions[0]

    items_data = _fetch_ddragon_json(
        f"https://ddragon.leagueoflegends.com/cdn/{latest}/data/en_US/item.json"
    )
    spells_data = _fetch_ddragon_json(
        f"https://ddragon.leagueoflegends.com/cdn/{latest}/data/en_US/summoner.json"
    )

    item_map: dict[int, str] = {}
    for item_id, payload in items_data.get("data", {}).items():
        try:
            item_map[int(item_id)] = payload.get("name", item_id)
        except ValueError:
            continue

    spell_map: dict[int, str] = {}
    for payload in spells_data.get("data", {}).values():
        key = payload.get("key")
        name = payload.get("name")
        if key is None or name is None:
            continue
        try:
            spell_map[int(key)] = name
        except ValueError:
            continue

    return item_map, spell_map