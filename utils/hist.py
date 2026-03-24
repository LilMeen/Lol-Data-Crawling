from pathlib import Path
import time
import os
import shutil

BASE_DIR = Path(__file__).resolve().parents[1]
BASE_DATA_DIR = BASE_DIR / 'data' 
CURRENT_HISTORY_FOLDER = None


def init_history_folder(force_new=False):
    global CURRENT_HISTORY_FOLDER

    if CURRENT_HISTORY_FOLDER is not None and not force_new:
        return CURRENT_HISTORY_FOLDER

    cur_timestamp = int(time.time())
    cur_timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(cur_timestamp))

    history_folder = BASE_DIR / 'data_hist' / str(cur_timestamp)
    history_folder.mkdir(parents=True, exist_ok=True)
    CURRENT_HISTORY_FOLDER = history_folder
    return history_folder


def dump_file_to_history(src_file):
    src_file = Path(src_file)

    if not src_file.exists() or not src_file.is_file():
        return

    try:
        relative_path = src_file.relative_to(BASE_DATA_DIR)
    except ValueError:
        return

    histdatapath = init_history_folder()
    dst_file = histdatapath / relative_path
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, dst_file)

def dump_data_to_history():
    histdatapath = init_history_folder()

    # Walk from data/ to data_hist/timestamp/
    for root, dirs, files in os.walk(BASE_DATA_DIR):
        for file in files:
            src_file = Path(root) / file
            dst_file = histdatapath / src_file.relative_to(BASE_DATA_DIR)
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)

    