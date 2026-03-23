from pathlib import Path
import time
import os
import shutil

BASE_DIR = Path(__file__).resolve().parents[1]
BASE_DATA_DIR = BASE_DIR / 'data' 


def init_history_folder():
    cur_timestamp = int(time.time())
    # Format cur_timestamp to yyyymmdd_hhmmss
    cur_timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(cur_timestamp))

    history_folder = BASE_DIR / 'data_hist' / str(cur_timestamp)
    history_folder.mkdir(parents=True, exist_ok=True)
    return history_folder

def dump_data_to_history():
    histdatapath = init_history_folder()

    # Walk from data/ to data_hist/timestamp/
    for root, dirs, files in os.walk(BASE_DATA_DIR):
        for file in files:
            src_file = Path(root) / file
            dst_file = histdatapath / src_file.relative_to(BASE_DATA_DIR)
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)

    