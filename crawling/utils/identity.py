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


def extract_opgg_region(player_link: str) -> str | None:
    if not player_link:
        return None

    parsed = urlparse(player_link)
    parts = [p for p in parsed.path.split("/") if p]
    # Expected OPGG path shape: /lol/summoners/{region}/{slug}
    if len(parts) >= 4 and parts[0] == "lol" and parts[1] == "summoners":
        return parts[2].lower()
    return None


def region_to_regional_routing(region: str | None) -> str:
    if not region:
        return "asia"

    region = region.lower()

    if region in {"na", "br", "lan", "las"}:
        return "americas"
    if region in {"kr", "jp"}:
        return "asia"
    if region in {"euw", "eune", "tr", "ru"}:
        return "europe"
    if region in {"oce", "ph", "sg", "th", "tw", "vn"}:
        return "sea"
    return "asia"
