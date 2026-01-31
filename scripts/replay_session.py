#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def _load_events(session_id: str):
    repo_root = Path(__file__).resolve().parents[1]
    api_dir = repo_root / "apps" / "api"
    sys.path.append(str(api_dir))

    from services.audit import iter_events  # noqa: E402

    return list(iter_events(session_id))


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: replay_session.py <session_id>")
        return 1

    session_id = sys.argv[1]
    events = _load_events(session_id)
    for event in events:
        print(f"{event.ts:.3f} {event.event_type} id={event.id}")
        print(json.dumps(event.payload_json, ensure_ascii=True, indent=2, sort_keys=True))
        if event.state_before_json is not None:
            print("state_before:")
            print(json.dumps(event.state_before_json, ensure_ascii=True, indent=2, sort_keys=True))
        if event.state_after_json is not None:
            print("state_after:")
            print(json.dumps(event.state_after_json, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
