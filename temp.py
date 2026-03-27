import argparse
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

from crawling.core.riot_client import RiotClient


QUEUE = "RANKED_SOLO_5x5"
PLATFORM_ROUTING = "na1"
REGIONAL_ROUTING = "americas"

PLATFORM_BASE_URL = f"https://{PLATFORM_ROUTING}.api.riotgames.com"
REGIONAL_BASE_URL = f"https://{REGIONAL_ROUTING}.api.riotgames.com"

TIER_SCORE = {
    "CHALLENGER": 9,
    "GRANDMASTER": 8,
    "MASTER": 7,
    "DIAMOND": 6,
    "EMERALD": 5,
    "PLATINUM": 4,
    "GOLD": 3,
    "SILVER": 2,
    "BRONZE": 1,
    "IRON": 0,
}

DIVISION_SCORE = {
    "I": 4,
    "II": 3,
    "III": 2,
    "IV": 1,
}


def load_env_file(env_path: Path) -> None:
    if not env_path.exists() or not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_api_key() -> str:
    base_dir = Path(__file__).resolve().parent
    load_env_file(base_dir / ".env")

    api_key = os.getenv("RIOT_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing RIOT_API_KEY. Set env var or add it to .env")
    if not api_key.startswith("RGAPI-"):
        raise RuntimeError("Invalid RIOT_API_KEY format.")
    return api_key


def fetch_apex_league(client: RiotClient, tier: str) -> list[dict[str, Any]]:
    path = f"/lol/league/v4/{tier.lower()}leagues/by-queue/{QUEUE}"
    payload = client.get(path, base_url=PLATFORM_BASE_URL)

    entries: list[dict[str, Any]] = payload.get("entries", []) if isinstance(payload, dict) else []
    for e in entries:
        e["tier"] = tier
        e.setdefault("rank", "I")
    return entries


def fetch_division_entries(
    client: RiotClient,
    tier: str,
    division: str,
    max_pages: int = 50,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        path = f"/lol/league/v4/entries/{QUEUE}/{tier}/{division}"
        batch = client.get(path, params={"page": page}, base_url=PLATFORM_BASE_URL)

        if not isinstance(batch, list) or not batch:
            break

        results.extend(batch)
    return results


def rank_key(entry: dict[str, Any]) -> tuple[Any, ...]:
    tier = str(entry.get("tier", "")).upper()
    rank = str(entry.get("rank", "IV")).upper()
    lp = int(entry.get("leaguePoints", 0))
    wins = int(entry.get("wins", 0))
    losses = int(entry.get("losses", 0))
    name = str(entry.get("summonerName", ""))
    return (
        -TIER_SCORE.get(tier, -1),
        -DIVISION_SCORE.get(rank, 0),
        -lp,
        -wins,
        losses,
        name,
    )


def deduplicate_by_summoner_id(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []

    for entry in entries:
        unique_id = str(
            entry.get("summonerId")
            or entry.get("puuid")
            or entry.get("summonerName")
            or ""
        )

        if not unique_id or unique_id in seen:
            continue
        seen.add(unique_id)
        deduped.append(entry)

    return deduped


def fallback_player_name(entry: dict[str, Any]) -> str:
    riot_id = str(entry.get("riotId", "")).strip()
    if riot_id:
        return riot_id

    summoner_name = str(entry.get("summonerName", "")).strip()
    if summoner_name:
        return summoner_name

    summoner_id = str(entry.get("summonerId", "")).strip()
    if summoner_id:
        return f"summoner:{summoner_id}"

    puuid = str(entry.get("puuid", "")).strip()
    if puuid:
        return f"puuid:{puuid[:16]}"

    return "unknown_summoner"


def build_top_na_ranked_list(client: RiotClient, top_n: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    for apex_tier in ("CHALLENGER", "GRANDMASTER", "MASTER"):
        apex_entries = fetch_apex_league(client, apex_tier)
        print(f"Fetched {len(apex_entries)} {apex_tier} players")
        entries.extend(apex_entries)

        entries = deduplicate_by_summoner_id(entries)
        entries.sort(key=rank_key)

        if len(entries) >= top_n:
            return entries[:top_n]

    # Fallback: pull DIAMOND I/II/III/IV pages until enough players.
    for division in ("I", "II", "III", "IV"):
        if len(entries) >= top_n:
            break
        diamond_entries = fetch_division_entries(client, "DIAMOND", division)
        print(f"Fetched {len(diamond_entries)} DIAMOND {division} players")
        entries.extend(diamond_entries)
        entries = deduplicate_by_summoner_id(entries)
        entries.sort(key=rank_key)

    return entries[:top_n]


def get_summoner_profile(client: RiotClient, encrypted_summoner_id: str) -> dict[str, Any]:
    sid = quote(encrypted_summoner_id, safe="")
    path = f"/lol/summoner/v4/summoners/{sid}"
    return client.get(path, base_url=PLATFORM_BASE_URL)


def get_account_by_puuid(client: RiotClient, puuid: str) -> dict[str, Any]:
    encoded_puuid = quote(puuid, safe="")
    path = f"/riot/account/v1/accounts/by-puuid/{encoded_puuid}"
    return client.get(path, base_url=REGIONAL_BASE_URL)


def build_opgg_link(game_name: str, tag_line: str) -> str:
    encoded_name = quote(game_name, safe="")
    encoded_tag = quote(tag_line, safe="")
    return f"https://op.gg/lol/summoners/na/{encoded_name}-{encoded_tag}"


def prepare_output_file(output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("", encoding="utf-8")


def append_output_line(file_handle: Any, line: str) -> None:
    file_handle.write(line + "\n")
    file_handle.flush()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch top NA ranked players (current ladder) and export a KR-like list file."
    )
    parser.add_argument("--top", type=int, default=900, help="Number of players to export (default: 900)")
    parser.add_argument(
        "--output",
        type=str,
        default="backup/na.txt",
        help="Output txt file path (default: backup/na.txt)",
    )
    parser.add_argument(
        "--resolve-riot-id",
        action="store_true",
        help="Resolve gameName#tagLine via extra API calls (slower, can hit rate limits).",
    )
    args = parser.parse_args()

    top_n = max(1, int(args.top))
    output_file = Path(args.output)

    api_key = get_api_key()
    client = RiotClient(api_key)

    print(f"Building NA top {top_n} player list...")
    ladder_entries = build_top_na_ranked_list(client, top_n)
    print(f"Collected {len(ladder_entries)} entries from current ladder")

    prepare_output_file(output_file)

    written_count = 0
    unresolved_count = 0

    with output_file.open("a", encoding="utf-8") as out_f:
        for idx, entry in enumerate(ladder_entries, start=1):
            tier = str(entry.get("tier", "")).upper()
            rank = str(entry.get("rank", "")).upper()
            lp = int(entry.get("leaguePoints", 0))
            fallback_name = fallback_player_name(entry)

            line_to_write = f"{fallback_name}{tier}:{rank}:{lp}LP\tN/A"

            if args.resolve_riot_id:
                summoner_id = str(entry.get("summonerId", ""))
                puuid = str(entry.get("puuid", ""))
                try:
                    if puuid:
                        account = get_account_by_puuid(client, puuid)
                    else:
                        profile = get_summoner_profile(client, summoner_id)
                        account = get_account_by_puuid(client, str(profile.get("puuid", "")))

                    game_name = str(account.get("gameName", "")).strip()
                    tag_line = str(account.get("tagLine", "")).strip()
                    if not game_name or not tag_line:
                        raise RuntimeError("Missing gameName/tagLine")

                    label = f"{game_name}#{tag_line}{tier}:{rank}:{lp}LP"
                    link = build_opgg_link(game_name, tag_line)
                    line_to_write = f"{label}\t{link}"
                except Exception:
                    unresolved_count += 1

            append_output_line(out_f, line_to_write)
            written_count += 1

            if idx % 50 == 0:
                print(f"Processed {idx}/{len(ladder_entries)} players | written: {written_count}")

    print(f"Done. Wrote {written_count} players to: {output_file}")
    if unresolved_count:
        print(f"Warning: {unresolved_count} players could not resolve Riot ID; filled with fallback name.")


if __name__ == "__main__":
    main()