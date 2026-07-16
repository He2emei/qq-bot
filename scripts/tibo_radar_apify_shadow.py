import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.apify_tibo_source import ApifyTiboSource, MAXIMEDUPRE_ACTOR_ID
from services.tibo_radar_shadow import run_shadow_check


def main():
    parser = argparse.ArgumentParser(description="Run one non-delivering Tibo Radar shadow check")
    parser.add_argument(
        "--state-path", default="data/tibo_radar_apify_shadow_state.json"
    )
    parser.add_argument(
        "--log-path", default="data/tibo_radar_apify_shadow_observations.jsonl"
    )
    args = parser.parse_args()

    token = os.getenv("TIBO_RADAR_APIFY_API_TOKEN", "").strip()
    if not token:
        parser.error("TIBO_RADAR_APIFY_API_TOKEN is required")

    source = ApifyTiboSource(
        api_token=token,
        handle=os.getenv("TIBO_RADAR_HANDLE", "thsottiaux"),
        actor_id=MAXIMEDUPRE_ACTOR_ID,
        base_url=os.getenv("TIBO_RADAR_APIFY_API_BASE_URL", "https://api.apify.com"),
        max_items=int(os.getenv("TIBO_RADAR_APIFY_MAX_ITEMS", "10")),
        run_timeout_seconds=int(
            os.getenv("TIBO_RADAR_APIFY_RUN_TIMEOUT_SECONDS", "180")
        ),
    )
    result = run_shadow_check(source, args.state_path, args.log_path)
    print(
        f"Tibo Radar shadow check succeeded: observed={len(result['observed_ids'])} "
        f"ids={result['observed_ids']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
