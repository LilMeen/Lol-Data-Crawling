from __future__ import annotations

import re
from urllib.parse import unquote, urlparse


def extract_riot_id(player_name: str, player_link: str) -> tuple[str, str] | None:
    if player_link:
        parsed = urlparse(player_link)
        slug = unquote(parsed.path.rstrip("/").split("/")[-1])
        if "-" in slug:
            game_name, tag_line = slug.rsplit("-", 1)
            if game_name and tag_line:
                return game_name, tag_line

    if "#" in player_name:
        game_name, rest = player_name.split("#", 1)
        tag_match = re.match(r"([A-Za-z0-9]{2,5})", rest)
        if game_name and tag_match:
            return game_name.strip(), tag_match.group(1)

    return None
