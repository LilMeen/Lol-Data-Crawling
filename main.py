import json
from crawling.v2.pipeline import CrawlingPipeline

def main() -> None:
    pipeline = CrawlingPipeline(
        matches_per_player=300,
        records_per_chunk=50,
    )
    result = pipeline.run(resume=True, start_index=51)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()