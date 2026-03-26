from __future__ import annotations

import argparse
import json

from crawling.pipeline import CrawlingPipeline
from preprocessing.pipeline import PreprocessingPipeline
from transforming.pipeline import TransformingPipeline


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run LoL data pipeline from a selected start step.",
    )
    parser.add_argument(
        "--step",
        choices=["crawling", "preprocessing", "transforming"],
        default="crawling",
        help="Step to start from.",
    )
    parser.add_argument(
        "--run-all",
        action="store_true",
        default=False,
        help="Run all pipelines from your selected step.",
    )

    parser.add_argument("--matches-per-player", type=int, default=500)
    parser.add_argument("--records-per-chunk", type=int, default=50)
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    parser.add_argument("--start-index", type=int, default=56)

    parser.add_argument("--max-months-ago", type=int, default=3)
    parser.add_argument("--preprocess-compression", default="snappy")
    parser.add_argument("--transform-compression", default="snappy")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result: dict[str, object] = {}

    if args.step == "crawling":
        crawling_pipeline = CrawlingPipeline(
            matches_per_player=args.matches_per_player,
            records_per_chunk=args.records_per_chunk,
        )
        result["crawling"] = crawling_pipeline.run(
            resume=args.resume,
            start_index=args.start_index,
        )
    if not args.run_all and args.step == "crawling":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.step in {"crawling", "preprocessing"}:
        preprocessing_pipeline = PreprocessingPipeline()
        preprocess_df, preprocess_path = preprocessing_pipeline.run(
            compression=args.preprocess_compression,
        )
        result["preprocessing"] = {
            "rows": len(preprocess_df),
            "output": str(preprocess_path),
        }
    if not args.run_all and args.step == "preprocessing":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.step in {"crawling", "preprocessing", "transforming"}:
        transforming_pipeline = TransformingPipeline()
        transform_df, transform_path, max_item_length = transforming_pipeline.run(
            compression=args.transform_compression,
            force_rebuild_preprocess=False,
            preprocess_compression=args.preprocess_compression,
        )
        result["transforming"] = {
            "rows": len(transform_df),
            "max_item_length": max_item_length,
            "output": str(transform_path),
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()