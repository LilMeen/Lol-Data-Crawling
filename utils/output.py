from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_FOLDER = BASE_DIR / 'data'
PLAYERS_CRAWL_DATA_FOLDER = BASE_DIR / 'data' / 'crawl' / 'players'
MATCHES_HISTORY_CRAWL_DATA_FOLDER = BASE_DIR / 'data' / 'crawl' / 'matches_history'

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

def save_players_crawl_summary(summary):
    filename = DATA_FOLDER / "players_crawl_summary.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for item in summary:
            f.write(f"{item['region']}\t{item['count']}\t{item['status']}\n")

def save_matches_to_file(match_history, region='kr'):
    filename = MATCHES_HISTORY_CRAWL_DATA_FOLDER / f"{region}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for row in match_history:
            matches = row.get('matches', [])
            if not matches:
                continue
            for match_url in matches:
                f.write(f"{row['player']}\t{match_url}\n")

def save_matches_crawl_summary(summary):
    filename = DATA_FOLDER / "matches_crawl_summary.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for item in summary:
            f.write(f"{item['region']}\t{item['match_count']}\n")