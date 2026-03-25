from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


_WINDOWS_INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'


class PipelineStorage:
    def __init__(self, base_dir: Path, records_per_chunk: int) -> None:
        self.base_dir = base_dir
        self.records_per_chunk = max(1, records_per_chunk)

        self.data_dir = self.base_dir / "data"
        self.data_crawl_dir = self.data_dir / "crawl"
        self.matches_v2_dir = self.data_crawl_dir / "matches_v2"
        self.checkpoint_dir = self.data_crawl_dir / "checkpoints"
        self.checkpoint_file = self.checkpoint_dir / "v2_pipeline_state.json"
        self.run_summary_file = self.data_dir / "matches_crawl_summary_v2.json"

        self.matches_v2_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self._chunk_state: dict[str, tuple[int, int]] = {}

    @staticmethod
    def sanitize_filename(name: str) -> str:
        safe = re.sub(_WINDOWS_INVALID_FILENAME_CHARS, "_", (name or "").strip())
        safe = safe.rstrip(" .")
        return safe or "unknown_player"

    def load_checkpoint(self) -> dict:
        if not self.checkpoint_file.exists():
            return {"nextIndex": 0}
        try:
            checkpoint = json.loads(self.checkpoint_file.read_text(encoding="utf-8"))
            if "nextIndex" in checkpoint:
                return checkpoint
            return {"nextIndex": 0}
        except json.JSONDecodeError:
            return {"nextIndex": 0}

    def save_checkpoint(self, checkpoint: dict) -> None:
        checkpoint["updatedAt"] = datetime.now(timezone.utc).isoformat()
        self.checkpoint_file.write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _get_chunk_state(self, safe_player: str) -> tuple[int, int]:
        cached = self._chunk_state.get(safe_player)
        if cached is not None:
            return cached

        player_dir = self.matches_v2_dir / safe_player
        player_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(player_dir.glob("part-*.jsonl"))

        if not files:
            state = (1, 0)
            self._chunk_state[safe_player] = state
            return state

        last_file = files[-1]
        chunk_index = int(last_file.stem.split("-")[-1])
        line_count = sum(1 for _ in last_file.open("r", encoding="utf-8"))
        state = (chunk_index, line_count)
        self._chunk_state[safe_player] = state
        return state

    def append_record_chunked(self, safe_player: str, record: dict) -> Path:
        chunk_index, line_count = self._get_chunk_state(safe_player)

        if line_count >= self.records_per_chunk:
            chunk_index += 1
            line_count = 0

        player_dir = self.matches_v2_dir / safe_player
        player_dir.mkdir(parents=True, exist_ok=True)
        chunk_file = player_dir / f"part-{chunk_index:04d}.jsonl"

        with chunk_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False))
            f.write("\n")

        self._chunk_state[safe_player] = (chunk_index, line_count + 1)
        return chunk_file

    def save_match_urls(self, safe_player: str, match_urls: list[str]) -> Path:
        out_file = self.matches_history_dir / f"{safe_player}.txt"
        with out_file.open("w", encoding="utf-8") as f:
            for url in match_urls:
                f.write(f"{url}\n")
        return out_file

    def save_run_summary(self, summary: dict) -> Path:
        self.run_summary_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.run_summary_file
