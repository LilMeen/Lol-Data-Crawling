import json
from pathlib import Path

def count_matches(folder_path: Path) -> int:
    total = 0
    for file in folder_path.glob("part-*.jsonl"):
        with file.open("r", encoding="utf-8") as f:
            for _ in f:
                total += 1
    return total

def main():
    matches_dir = Path("data/crawl/matches_v2")
    total_matches = 0

    count_dict = {}
    for player_dir in matches_dir.iterdir():
        if player_dir.is_dir():
            player_match_count = count_matches(player_dir)
            count_dict[player_dir.name] = player_match_count
            total_matches += player_match_count

    print(f"Total matches across all players: {total_matches}")
    print("Match count per player:")
    # Order by index number prefix in player directory name (e.g., "1.PlayerName", "2.PlayerName", etc.)
    for player in sorted(count_dict.keys(), key=lambda x: int(x.split(".")[0])):
        count = count_dict[player]
        print(f"{player}: {count}")

if __name__ == "__main__":
    main()