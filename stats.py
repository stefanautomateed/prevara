"""
Persistent stats tracking for runs and submissions.
Stores counts in logs/stats.json.
"""
import json
import os
from pathlib import Path
from typing import Dict


STATS_PATH = Path('logs/stats.json')


DEFAULT_STATS: Dict[str, int] = {
    'manual_triggers': 0,                # times manual run was initiated
    'scheduler_triggers': 0,             # times scheduler job fired (once per job execution)
    'total_submissions_attempted': 0,    # total URL submissions attempted
    'total_successful_submissions': 0,   # total URL submissions succeeded
    'total_failed_submissions': 0        # total URL submissions failed
}


def _ensure_storage():
    os.makedirs('logs', exist_ok=True)
    if not STATS_PATH.exists():
        with open(STATS_PATH, 'w') as f:
            json.dump(DEFAULT_STATS, f)


def load_stats() -> Dict[str, int]:
    _ensure_storage()
    try:
        with open(STATS_PATH, 'r') as f:
            data = json.load(f)
            # ensure all keys exist
            for k, v in DEFAULT_STATS.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return DEFAULT_STATS.copy()


def save_stats(stats: Dict[str, int]):
    _ensure_storage()
    with open(STATS_PATH, 'w') as f:
        json.dump(stats, f)


def increment(key: str, amount: int = 1):
    stats = load_stats()
    stats[key] = int(stats.get(key, 0)) + amount
    save_stats(stats)


def increment_manual_trigger():
    increment('manual_triggers', 1)


def increment_scheduler_trigger():
    increment('scheduler_triggers', 1)


def increment_submission_attempts(count: int = 1):
    increment('total_submissions_attempted', count)


def increment_successes(count: int = 1):
    increment('total_successful_submissions', count)


def increment_failures(count: int = 1):
    increment('total_failed_submissions', count)


