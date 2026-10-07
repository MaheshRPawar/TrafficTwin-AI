#!/usr/bin/env python3
"""
TrafficTwin AI — GPS Event Stream Replay Utility (Module M4)

Reads a simulated GPS JSONL stream, validates each event against the
normalized schema, replays observations in chronological order, and
tracks live vehicle state.

Usage:
    python experiments/replay_gps.py data/output/gps/normal.jsonl
    python experiments/replay_gps.py data/output/gps/rush.jsonl --limit 20
    python experiments/replay_gps.py data/output/gps/normal.jsonl --quiet
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.stream.gps_event import validate_gps_event


def replay_stream(
    file_path: Path,
    limit: int | None = None,
    quiet: bool = False,
    delay_s: float = 0.0,
) -> dict:
    """Read and replay GPS events from a JSONL file, validating each record."""
    path = Path(file_path)
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    total_events = 0
    valid_events = 0
    invalid_events = 0
    unique_vehicles = set()
    first_timestamp = None
    last_timestamp = None
    last_known_state = {}

    with open(path, encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue

            total_events += 1

            # Parse JSON line
            try:
                event = json.loads(line_str)
            except json.JSONDecodeError as exc:
                invalid_events += 1
                if not quiet:
                    print(f"  [INVALID JSON] line {total_events}: {exc}")
                continue

            # Validate schema
            is_valid, error_msg = validate_gps_event(event)
            if not is_valid:
                invalid_events += 1
                if not quiet:
                    print(f"  [VALIDATION FAIL] line {total_events}: {error_msg}")
                continue

            valid_events += 1
            ts = float(event["timestamp"])
            vid = event["vehicle_id"]
            unique_vehicles.add(vid)
            last_known_state[vid] = event

            if first_timestamp is None:
                first_timestamp = ts
            last_timestamp = ts

            # Print readable event line
            if not quiet and (limit is None or valid_events <= limit):
                print(
                    f"timestamp={ts:5.1f}s vehicle={vid:<10} type={event['vehicle_type']:<5} "
                    f"speed={event['speed_kmph']:5.1f} km/h pos=({event['x']:6.1f},{event['y']:6.1f}) "
                    f"lane={event['lane_id']}"
                )

            if delay_s > 0:
                time.sleep(delay_s)

            if limit is not None and valid_events >= limit and not quiet:
                print(f"  ... [preview stopped at limit={limit}] ...")
                break

    summary = {
        "file": str(path),
        "total_events": total_events,
        "valid_events": valid_events,
        "invalid_events": invalid_events,
        "unique_vehicles": len(unique_vehicles),
        "start_time_s": first_timestamp if first_timestamp is not None else 0.0,
        "end_time_s": last_timestamp if last_timestamp is not None else 0.0,
        "active_vehicles_at_end": len(last_known_state),
    }

    # Print summary block
    print("\n=== Replay Summary ===")
    print(f"File:                   {summary['file']}")
    print(f"Events replayed:        {summary['valid_events']} / {summary['total_events']}")
    print(f"Invalid events:         {summary['invalid_events']}")
    print(f"Unique vehicles:        {summary['unique_vehicles']}")
    print(f"Start time:             {summary['start_time_s']:.1f}s")
    print(f"End time:               {summary['end_time_s']:.1f}s")
    print(f"Active vehicles at end: {summary['active_vehicles_at_end']}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay simulated GPS event stream")
    parser.add_argument(
        "file",
        type=Path,
        help="Path to JSONL stream file to replay",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of lines displayed in terminal",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-event printing and show summary only",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between replaying events",
    )
    args = parser.parse_args()

    replay_stream(
        file_path=args.file,
        limit=args.limit,
        quiet=args.quiet,
        delay_s=args.delay,
    )


if __name__ == "__main__":
    main()
