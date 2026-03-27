import os
from pathlib import Path
from typing import Any

from crawling.config.constants import QUEUE_TYPE_MAP
from crawling.core.riot_client import RiotClient
from crawling.crawl.crawl import (
    crawl_players,
    get_account_by_riot_id,
    get_match_detail,
    get_match_ids,
    get_match_timeline,
)
from crawling.crawl.load import load_ddragon_maps, load_player_from_file
from crawling.output.storage import PipelineStorage
from crawling.transform.match_record import (
    build_match_record,
    find_participant,
)
from crawling.utils.identity import extract_riot_id
from crawling.utils.identity import extract_opgg_region, region_to_regional_routing
from crawling.utils.time import check_exceed_time_limit_3_months
from crawling.utils.time import check_exceed_time_limit_3_months


class CrawlingPipeline:
    """End-to-end crawling pipeline with incremental writes and resume checkpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        matches_per_player: int = 20,
        records_per_chunk: int = 50,
    ) -> None:
        self.base_dir = Path(__file__).resolve().parents[1]

        self.matches_per_player = max(1, matches_per_player)
        self.records_per_chunk = max(1, records_per_chunk)

        resolved_key = api_key or self._load_api_key()
        self.client = RiotClient(resolved_key)
        self.item_map, self.spell_map = load_ddragon_maps()
        self.storage = PipelineStorage(
            base_dir=self.base_dir,
            records_per_chunk=self.records_per_chunk,
        )

    def _load_dotenv_file(self, dotenv_path: str = ".env") -> None:
        path = self.base_dir / dotenv_path
        if not path.exists() or not path.is_file():
            return

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)

    def _load_api_key(self) -> str:
        self._load_dotenv_file()
        api_key = os.getenv("RIOT_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing Riot API key. Set RIOT_API_KEY in environment or .env file."
            )
        if not api_key.startswith("RGAPI-"):
            raise RuntimeError("Invalid RIOT_API_KEY format. Expected key starting with RGAPI-.")
        return api_key

    def run(self, resume: bool = True, start_index: int | None = None) -> dict[str, Any]:
        """Run crawl pipeline.

        start_index is 1-based user position in the crawled player list.
        If provided, it takes precedence over resume checkpoint.
        """
        players = load_player_from_file(self.base_dir / "data" / "crawl" / "players" / "kr.txt")
        total_players = len(players)
        checkpoint = self.storage.load_checkpoint()

        if start_index is not None:
            if start_index < 1:
                raise ValueError("start_index must be >= 1 (1-based user position).")
            if start_index > total_players:
                raise ValueError(
                    f"start_index={start_index} is greater than total players={total_players}."
                )
            start_user_no = start_index
        elif resume:
            start_user_no = int(checkpoint.get("nextIndex", 1))
            if start_user_no < 1:
                start_user_no = 1
            if start_user_no > total_players:
                summary = {
                    "total_players": total_players,
                    "start_index": start_user_no,
                    "match_count": 0,
                    "players_success": 0,
                    "players_failed": 0,
                    "message": "Nothing to run. Resume checkpoint is already beyond available players.",
                }
                self.storage.save_run_summary(summary)
                return {
                    "status": "success",
                    "summary": summary,
                    "checkpoint": str(self.storage.checkpoint_file),
                    "matches_dir": str(self.storage.matches_v2_dir),
                }
        else:
            start_user_no = 1

        success_count = 0
        failed_count = 0
        match_count = 0

        for user_no, player_data in enumerate(players, start=1):
            if user_no < start_user_no:
                continue

            player_name = player_data.get("name", "")
            player_link = player_data.get("link", "")
            riot_id = extract_riot_id(player_name, player_link)
            opgg_region = extract_opgg_region(player_link)
            regional_routing = region_to_regional_routing(opgg_region)
            regional_base_url = f"https://{regional_routing}.api.riotgames.com"
            safe_player = self.storage.sanitize_filename(f"{user_no}.{player_name}")

            if riot_id is None:
                failed_count += 1
                checkpoint["nextIndex"] = user_no + 1
                self.storage.save_checkpoint(checkpoint)
                continue

            game_name, tag_line = riot_id

            try:
                print(f"[CrawlingPipeline] Processing player {user_no}/{total_players}: {game_name}#{tag_line}")
                account = get_account_by_riot_id(
                    self.client,
                    game_name,
                    tag_line,
                    base_url=regional_base_url,
                )
                puuid = account["puuid"]
                match_ids = get_match_ids(
                    self.client,
                    puuid,
                    count=self.matches_per_player,
                    base_url=regional_base_url,
                )
                print(f"[CrawlingPipeline] Found {len(match_ids)} matches for player {game_name}#{tag_line}")

                account_label = (
                    f"{account.get('gameName', game_name)}#"
                    f"{account.get('tagLine', tag_line)}"
                )


                for match_id in match_ids:
                    detail = get_match_detail(self.client, match_id, base_url=regional_base_url)
                    timeline = get_match_timeline(self.client, match_id, base_url=regional_base_url)
                    participant = find_participant(detail, puuid)

                    time = int(detail.get("info", {}).get("gameEndTimestamp", 0))
                    is_exceed = check_exceed_time_limit_3_months(time)
                    if is_exceed:
                        break

                    record = build_match_record(
                        account_label=account_label,
                        game_name=account.get("gameName", game_name),
                        tag_line=account.get("tagLine", tag_line),
                        match_detail=detail,
                        timeline=timeline,
                        participant=participant,
                        item_map=self.item_map,
                        spell_map=self.spell_map,
                        queue_type_map=QUEUE_TYPE_MAP,
                    )

                    self.storage.append_record_chunked(safe_player, record)
                    match_count += 1
                success_count += 1
            except Exception as exc:
                failed_count += 1
                print(
                    f"[CrawlingPipeline] Failed player '{player_name}' "
                    f"({game_name}#{tag_line}): {exc}"
                )
            finally:
                checkpoint["nextIndex"] = user_no + 1
                self.storage.save_checkpoint(checkpoint)

        summary = {
            "total_players": total_players,
            "start_index": start_user_no,
            "match_count": match_count,
            "players_success": success_count,
            "players_failed": failed_count,
        }

        self.storage.save_run_summary(summary)

        return {
            "status": "success",
            "summary": summary,
            "checkpoint": str(self.storage.checkpoint_file),
            "matches_dir": str(self.storage.matches_v2_dir),
        }
