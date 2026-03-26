from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from preprocessing.config.constants import PREPROCESSED_MATCHES_PATH
from preprocessing.item_hierarchy.full_build import create_full_build
from preprocessing.item_hierarchy.load_item_hierarchy import load_item_tree
from crawling.utils.time import check_exceed_time_limit
from transforming.config.constants import RAW_DATA_DIR

class PreprocessingPipeline:
    def __init__(self, raw_data_dir: Path | str = RAW_DATA_DIR):
        self.raw_data_dir = Path(raw_data_dir)
        self.constraints = {
            "max_days_ago": 120,
            "type": ['Ranked Solo/Duo', 'Ranked Flex'],
            "result": ['Win', 'Defeat'],
        }

    @staticmethod
    def _load_json_array(file_path: Path) -> list[dict]:
        with file_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if isinstance(payload, list):
            return [record for record in payload if isinstance(record, dict)]
        if isinstance(payload, dict):
            return [payload]
        return []

    @staticmethod
    def _load_jsonl(file_path: Path) -> list[dict]:
        records: list[dict] = []
        with file_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    records.append(payload)
        return records

    def load_raw_records(self) -> list[dict]:
        if not self.raw_data_dir.exists() or not self.raw_data_dir.is_dir():
            raise ValueError(f"Invalid raw data directory: {self.raw_data_dir}")

        all_records: list[dict] = []
        for file_path in self.raw_data_dir.rglob("*"):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            if suffix == ".json":
                all_records.extend(self._load_json_array(file_path))
            elif suffix == ".jsonl":
                all_records.extend(self._load_jsonl(file_path))

        return all_records

    @staticmethod
    def filter_recent_matches(records_df: pd.DataFrame, max_days_ago: int = 90) -> pd.DataFrame:
        if "meta" not in records_df.columns:
            return records_df.copy()

        filtered_df = records_df.copy()
        filtered_df = filtered_df[filtered_df["meta"].apply(
            lambda meta: check_exceed_time_limit(meta.get("gameCreation", 0), max_days=max_days_ago))
        ]
        return filtered_df
    
    @staticmethod
    def filter_typed_matches(records_df: pd.DataFrame, allowed_types: list[str]) -> pd.DataFrame:
        if "type" not in records_df.columns:
            return records_df.copy()
        
        filtered_df = records_df.copy()
        filtered_df = filtered_df[filtered_df["type"].isin(allowed_types)]
        return filtered_df
    
    @staticmethod
    def filter_result_matches(records_df: pd.DataFrame, allowed_results: list[str]) -> pd.DataFrame:
        if "result" not in records_df.columns:
            return records_df.copy()
        
        filtered_df = records_df.copy()
        filtered_df = filtered_df[filtered_df["result"].isin(allowed_results)]
        return filtered_df

    @staticmethod
    def add_full_build(records_df: pd.DataFrame, item_tree: list[dict]) -> pd.DataFrame:
        data = records_df.copy()
        if "itemBuilds" not in data.columns:
            data["itemBuilds"] = [[] for _ in range(len(data.index))]

        data["fullBuilds"] = data["itemBuilds"].apply(
            lambda items: create_full_build(items, item_tree)
        )
        return data

    @staticmethod
    def save_parquet(
        dataframe: pd.DataFrame,
        output_path: Path | str,
        compression: str | None = "snappy",
    ) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_parquet(output, index=False, compression=compression)
        return output

    def run(
        self,
        output_path: Path | str | None = None,
        compression: str | None = "snappy",
    ) -> tuple[pd.DataFrame, Path]:
        raw_records = self.load_raw_records()
        records_df = pd.DataFrame(raw_records)

        filtered_df = self.filter_recent_matches(records_df, max_days_ago=self.constraints["max_days_ago"])
        filtered_df = self.filter_typed_matches(filtered_df, allowed_types=self.constraints["type"])
        filtered_df = self.filter_result_matches(filtered_df, allowed_results=self.constraints["result"])

        item_tree = load_item_tree()
        preprocessed_df = self.add_full_build(filtered_df, item_tree)

        if output_path is None:
            output_path = PREPROCESSED_MATCHES_PATH

        saved_path = self.save_parquet(
            preprocessed_df,
            output_path,
            compression=compression,
        )
        return preprocessed_df, saved_path
