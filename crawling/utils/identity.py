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
        tag_name = rest.split('Lv.')[0].strip()  # Remove level info if present
        if game_name and tag_name:
            return game_name.strip(), tag_name.strip()
    return None
