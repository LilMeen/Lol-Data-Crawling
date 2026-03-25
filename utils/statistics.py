from pathlib import Path

def count_matches(folder_path):
    folder_path = Path(folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Invalid folder path: {folder_path}")
        return 0

    total_matches = 0
    for file in folder_path.glob("*.txt"):
        if file.is_file():
            with open(file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                total_matches += len(lines)

    return total_matches