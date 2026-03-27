from __future__ import annotations

from pathlib import Path

import pandas as pd

from preprocessing.pipeline import PreprocessingPipeline
from transforming.config.constants import (
    PREPROCESSED_MATCHES_PATH,
    TRANSFORM_OUTPUT_DIR,
)
from transforming.transform.table_schema import build_training_table
from transforming.validate.validate_data import validate_data


class TransformingPipeline:
    def __init__(
        self,
        preprocessed_path: Path | str = PREPROCESSED_MATCHES_PATH,
    ):
        self.preprocessed_path = Path(preprocessed_path)
        self.preprocessing_pipeline = PreprocessingPipeline()

    def load_preprocessed_records(
        self,
        force_rebuild_preprocess: bool = False,
        preprocess_compression: str | None = "snappy",
    ) -> pd.DataFrame:
        if force_rebuild_preprocess or not self.preprocessed_path.exists():
            preprocessed_df, _ = self.preprocessing_pipeline.run(
                output_path=self.preprocessed_path,
                compression=preprocess_compression,
            )
            return preprocessed_df

        return pd.read_parquet(self.preprocessed_path)

    def transform(self, records_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        transformed_df, max_item_length = build_training_table(
            records_df=records_df,
        )
        return transformed_df, max_item_length

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
        force_rebuild_preprocess: bool = False,
        preprocess_compression: str | None = "snappy",
    ) -> tuple[pd.DataFrame, Path, int]:
        records_df = self.load_preprocessed_records(
            force_rebuild_preprocess=force_rebuild_preprocess,
            preprocess_compression=preprocess_compression,
        )
        transformed_df, max_item_length = self.transform(records_df)

        if output_path is None:
            output_path = TRANSFORM_OUTPUT_DIR / "matches_encoded.parquet"

        saved_path = self.save_parquet(
            transformed_df,
            output_path,
            compression=compression,
        )

        return transformed_df, saved_path, max_item_length