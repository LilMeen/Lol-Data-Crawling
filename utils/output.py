from pathlib import Path
import re
from utils.hist import dump_file_to_history


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_FOLDER = BASE_DIR / 'data'
PLAYERS_CRAWL_DATA_FOLDER = BASE_DIR / 'data' / 'crawl' / 'players'
MATCHES_HISTORY_CRAWL_DATA_FOLDER = BASE_DIR / 'data' / 'crawl' / 'matches_history'


_WINDOWS_INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'


def _sanitize_filename(name: str) -> str:
    """Return a filesystem-safe filename (without extension)."""
    safe = re.sub(_WINDOWS_INVALID_FILENAME_CHARS, '_', (name or '').strip())
    safe = safe.rstrip(' .')
    return safe or 'unknown_player'

def init_output_folder():
    PLAYERS_CRAWL_DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    MATCHES_HISTORY_CRAWL_DATA_FOLDER.mkdir(parents=True, exist_ok=True)

def clean_output_folder():
    for file in PLAYERS_CRAWL_DATA_FOLDER.glob("*"):
        if file.is_file():
            file.unlink()
    for file in MATCHES_HISTORY_CRAWL_DATA_FOLDER.glob("*"):
        if file.is_file():
            file.unlink()

def save_players_to_file(players, region):
    filename = PLAYERS_CRAWL_DATA_FOLDER / f"{region}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for p in players:
            f.write(f"{p['name']}\t{p['link']}\n")
    dump_file_to_history(filename)

def save_players_crawl_summary(summary):
    filename = DATA_FOLDER / "players_crawl_summary.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for item in summary:
            f.write(f"{item['region']}\t{item['count']}\t{item['status']}\n")
    dump_file_to_history(filename)

def save_matches_to_file(player, matches):
    safe_player = _sanitize_filename(player)
    filename = MATCHES_HISTORY_CRAWL_DATA_FOLDER / f"{safe_player}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for match_url in matches:
            f.write(f"{match_url}\n")
    dump_file_to_history(filename)

def save_matches_crawl_summary(summary):
    filename = DATA_FOLDER / "matches_crawl_summary.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for item in summary:
            f.write(f"{item['region']}\t{item['match_count']}\n")
    dump_file_to_history(filename)