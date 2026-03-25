from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from crawling.v2.utils.time import format_relative_time


def build_opgg_match_url(game_name: str, tag_line: str, match_id: str) -> str:
    encoded_name = quote(game_name, safe="")
    encoded_tag = quote(tag_line, safe="")
    encoded_match = quote(match_id, safe="")
    return f"https://op.gg/lol/summoners/kr/{encoded_name}-{encoded_tag}/matches/{encoded_match}"


def find_participant(match_detail: dict[str, Any], puuid: str) -> dict[str, Any]:
    participants = match_detail.get("info", {}).get("participants", [])
    for participant in participants:
        if participant.get("puuid") == puuid:
            return participant
    raise RuntimeError("Could not find participant by puuid in match detail.")


def build_item_builds_from_timeline(
    timeline: dict[str, Any], participant_id: int, item_map: dict[int, str]
) -> list[str]:
    builds: list[int] = []
    frames = timeline.get("info", {}).get("frames", [])

    for frame in frames:
        for event in frame.get("events", []):
            if int(event.get("participantId", 0)) != participant_id:
                continue

            event_type = event.get("type")
            if event_type == "ITEM_PURCHASED":
                item_id = int(event.get("itemId", 0))
                if item_id > 0:
                    builds.append(item_id)
            elif event_type == "ITEM_UNDO":
                before_id = int(event.get("beforeId", 0))
                if before_id <= 0:
                    continue
                for idx in range(len(builds) - 1, -1, -1):
                    if builds[idx] == before_id:
                        del builds[idx]
                        break

    return [item_map.get(item_id, str(item_id)) for item_id in builds]


def build_match_record(
    account_label: str,
    game_name: str,
    tag_line: str,
    match_detail: dict[str, Any],
    timeline: dict[str, Any],
    participant: dict[str, Any],
    item_map: dict[int, str],
    spell_map: dict[int, str],
    queue_type_map: dict[int, str],
) -> dict[str, Any]:
    kills = int(participant.get("kills", 0))
    deaths = int(participant.get("deaths", 0))
    assists = int(participant.get("assists", 0))
    kda_ratio = round((kills + assists) / max(1, deaths), 2)

    spell_1 = spell_map.get(
        int(participant.get("summoner1Id", 0)), str(participant.get("summoner1Id", ""))
    )
    spell_2 = spell_map.get(
        int(participant.get("summoner2Id", 0)), str(participant.get("summoner2Id", ""))
    )

    info = match_detail.get("info", {})
    metadata = match_detail.get("metadata", {})
    match_id = metadata.get("matchId", "")
    queue_id = int(info.get("queueId", 0))

    participant_id = int(participant.get("participantId", 0))
    item_builds = build_item_builds_from_timeline(
        timeline=timeline,
        participant_id=participant_id,
        item_map=item_map,
    )

    return {
        "player": account_label,
        "matchUrl": build_opgg_match_url(game_name, tag_line, match_id),
        "matchId": match_id,
        "type": queue_type_map.get(queue_id, f"Queue {queue_id}"),
        "time": format_relative_time(
            int(info.get("gameEndTimestamp", info.get("gameCreation", 0)))
        ),
        "result": "Victory" if participant.get("win") else "Defeat",
        "champion": str(participant.get("championName", "")).lower(),
        "spell": [spell_1, spell_2],
        "kda": {
            "kills": kills,
            "deaths": deaths,
            "assists": assists,
        },
        "kdaRatio": kda_ratio,
        "position": participant.get("teamPosition")
        or participant.get("individualPosition")
        or "Unknown",
        "itemBuilds": item_builds,
        "_meta": {
            "matchId": match_id,
            "gameCreation": info.get("gameCreation"),
            "capturedAt": datetime.now(timezone.utc).isoformat(),
        },
    }
