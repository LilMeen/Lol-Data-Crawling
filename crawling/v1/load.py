
# LOAD PLAYER DATA FROM FILE
# ============================
# File name: {region}.txt (e.g., kr.txt, na.txt, etc.)
#
# File structure:
# players.txt
# player_name1    player_link1
# player_name2    player_link2
# ...
# ============================
from pathlib import Path


def load_players_from_file(file_path):
    players = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            name, link = line.strip().split("\t")
            players.append({"name": name, "link": link})
    return players


# LOAD MATCH HISTORY DATA FROM FOLDER
# ====================================
# Folder structure:
# matches_history/
#   player_name1.txt
#   player_name2.txt
#   ...
#
# Each player_name.txt contains:
# match_url1
# match_url2
# ...
# ====================================
def load_matches_from_folder(folder_path):
    matches_data = {}
    folder_path = Path(folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Invalid folder path: {folder_path}")
        return matches_data

    for file in folder_path.glob("*.txt"):
        if file.is_file():
            player_name = file.stem
            with open(file, "r", encoding="utf-8") as f:
                match_urls = [line.strip() for line in f if line.strip()]
                matches_data[player_name] = match_urls

    return matches_data