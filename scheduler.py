"""
Scheduler for automated form filling.
Runs form filling at specified times throughout the day.
"""
import asyncio
import logging
import os
import schedule
import random
from datetime import timedelta
import time
from datetime import datetime
from dotenv import load_dotenv
from form_filler import run_single_form_fill
from privacy_utils import PrivacyUtils
from stats import (
    increment_scheduler_trigger,
    increment_submission_attempts,
    increment_successes,
    increment_failures
)


# Load environment variables
load_dotenv()

# Ensure logs directory exists before configuring file handlers
os.makedirs('logs', exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Holds the currently scheduled times (as HH:MM strings) for status/UI
CURRENT_SCHEDULE_TIMES = []


def get_config():
    """Load configuration from environment variables."""
    # Support both TARGET_URL (single) and TARGET_URLS (multiple)
    target_urls_str = os.getenv('TARGET_URLS', os.getenv('TARGET_URL', 'https://noro.rs/'))
    target_urls = [url.strip() for url in target_urls_str.split(',')]

    return {
        'target_urls': target_urls,
        'schedule_times': os.getenv('SCHEDULE_TIMES', '10:00,14:00,18:00').split(','),
        'headless': os.getenv('HEADLESS', 'false').lower() == 'true',
        'min_delay': float(os.getenv('MIN_DELAY', '1')),
        'max_delay': float(os.getenv('MAX_DELAY', '3')),
        'random_schedule': os.getenv('RANDOM_SCHEDULE', 'false').lower() == 'true',
        'runs_per_day': int(os.getenv('RUNS_PER_DAY', '8')),
        'time_window_start': os.getenv('TIME_WINDOW_START', '09:00'),
        'time_window_end': os.getenv('TIME_WINDOW_END', '22:00'),
        'min_gap_minutes': int(os.getenv('MIN_GAP_MINUTES', '45')),
        'proxy': os.getenv('PROXY_URL', ''),
        'schedule_jitter_minutes': int(os.getenv('SCHEDULE_JITTER_MINUTES', '10'))
    }


def _parse_hhmm(hhmm: str) -> int:
    """Convert HH:MM to minutes since midnight."""
    hh, mm = hhmm.split(':')
    return int(hh) * 60 + int(mm)


def _format_hhmm(minutes_since_midnight: int) -> str:
    """Convert minutes since midnight to HH:MM string."""
    minutes_since_midnight %= 24 * 60
    hh = minutes_since_midnight // 60
    mm = minutes_since_midnight % 60
    return f"{hh:02d}:{mm:02d}"


def generate_random_times(runs_per_day: int, start_hhmm: str, end_hhmm: str, min_gap_minutes: int) -> list:
    """Generate a list of HH:MM timestamps randomly distributed in a window with minimal gaps."""
    start_min = _parse_hhmm(start_hhmm)
    end_min = _parse_hhmm(end_hhmm)
    if end_min <= start_min:
        end_min += 24 * 60  # allow overnight windows

    picks = []
    attempts = 0
    max_attempts = runs_per_day * 100

    while len(picks) < runs_per_day and attempts < max_attempts:
        attempts += 1
        candidate = random.randint(start_min, end_min - 1)
        # Check minimal gap with existing picks
        ok = True
        for p in picks:
            if abs(candidate - p) < min_gap_minutes:
                ok = False
                break
        if ok:
            picks.append(candidate)

    picks.sort()
    # Normalize back to 0-24h range
    times = [_format_hhmm(p % (24 * 60)) for p in picks]
    return times


def job():
    """Job to run at scheduled times."""
    logger.info("=" * 60)
    logger.info(f"Starting scheduled form fill at {datetime.now()}")
    logger.info("=" * 60)

    # Count this scheduler trigger once per job execution
    try:
        increment_scheduler_trigger()
    except Exception as e:
        logger.warning(f"Could not persist scheduler trigger stat: {e}")

    config = get_config()

    # Run form fills for all target URLs
    for target_url in config['target_urls']:
        try:
            logger.info(f"Processing {target_url}")
            
            # Get randomized delays for this run
            min_delay, max_delay = PrivacyUtils.get_random_delays(
                config['min_delay'], 
                config['max_delay'], 
                variance=0.5
            )
            logger.info(f"Using randomized delays: {min_delay}s - {max_delay}s")

            # Run the async form filling with proxy if configured
            result = asyncio.run(run_single_form_fill(
                target_url=target_url,
                headless=config['headless'],
                min_delay=min_delay,
                max_delay=max_delay,
                proxy=config['proxy'] if config['proxy'] else None
            ))

            try:
                increment_submission_attempts(1)
            except Exception:
                pass

            if result:
                logger.info(f"Form fill for {target_url} completed successfully!")
                try:
                    increment_successes(1)
                except Exception:
                    pass
            else:
                logger.error(f"Form fill for {target_url} failed!")
                try:
                    increment_failures(1)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error processing {target_url}: {e}")
            try:
                increment_submission_attempts(1)
                increment_failures(1)
            except Exception:
                pass

    logger.info("=" * 60)


def setup_scheduler():
    """Setup the schedule based on configuration."""
    config = get_config()

    logger.info("Setting up scheduler...")
    logger.info(f"Target URLs: {', '.join(config['target_urls'])}")
    logger.info(f"Headless mode: {config['headless']}")

    # Clear all existing jobs from previous runs in this process
    schedule.clear()

    if config['random_schedule']:
        # Generate today's random times
        times = generate_random_times(
            runs_per_day=config['runs_per_day'],
            start_hhmm=config['time_window_start'],
            end_hhmm=config['time_window_end'],
            min_gap_minutes=config['min_gap_minutes']
        )
        CURRENT_SCHEDULE_TIMES.clear()
        CURRENT_SCHEDULE_TIMES.extend(times)

        logger.info(f"Random scheduling enabled. Runs per day: {config['runs_per_day']}")
        logger.info(f"Time window: {config['time_window_start']} - {config['time_window_end']}")
        logger.info(f"Minimum gap (minutes): {config['min_gap_minutes']}")
        logger.info(f"Schedule jitter: ±{config['schedule_jitter_minutes']} minutes")
        logger.info(f"Generated times: {', '.join(times)}")

        for t in times:
            # Add random jitter to each scheduled time
            jittered_time = PrivacyUtils.add_random_jitter(t, config['schedule_jitter_minutes'])
            schedule.every().day.at(jittered_time).do(job).tag('random_runs')
            logger.info(f"Scheduled job at {t} (jittered to {jittered_time})")

        # Schedule a daily regeneration just after midnight
        def regenerate():
            logger.info("Regenerating random schedule for new day...")
            schedule.clear('random_runs')
            new_times = generate_random_times(
                runs_per_day=config['runs_per_day'],
                start_hhmm=config['time_window_start'],
                end_hhmm=config['time_window_end'],
                min_gap_minutes=config['min_gap_minutes']
            )
            CURRENT_SCHEDULE_TIMES.clear()
            CURRENT_SCHEDULE_TIMES.extend(new_times)
            logger.info(f"New times: {', '.join(new_times)}")
            for t in new_times:
                jittered_time = PrivacyUtils.add_random_jitter(t, config['schedule_jitter_minutes'])
                schedule.every().day.at(jittered_time).do(job).tag('random_runs')
                logger.info(f"Scheduled job at {t} (jittered to {jittered_time})")

        schedule.every().day.at('00:05').do(regenerate).tag('random_regen')
        logger.info("Scheduled daily random regeneration at 00:05")

    else:
        logger.info(f"Fixed schedule times: {config['schedule_times']}")
        logger.info(f"Schedule jitter: ±{config['schedule_jitter_minutes']} minutes")
        CURRENT_SCHEDULE_TIMES.clear()
        CURRENT_SCHEDULE_TIMES.extend(config['schedule_times'])
        
        for time_str in config['schedule_times']:
            time_str = time_str.strip()
            # Add random jitter to fixed times too
            jittered_time = PrivacyUtils.add_random_jitter(time_str, config['schedule_jitter_minutes'])
            schedule.every().day.at(jittered_time).do(job).tag('fixed_runs')
            logger.info(f"Scheduled job at {time_str} (jittered to {jittered_time})")

    logger.info("Scheduler setup complete!")
    logger.info("Waiting for scheduled times...")


def run_scheduler():
    """Run the scheduler loop."""
    setup_scheduler()

    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def get_current_schedule_times():
    """Return the currently active daily schedule times (HH:MM)."""
    if CURRENT_SCHEDULE_TIMES:
        return list(CURRENT_SCHEDULE_TIMES)
    # Fallback to configured fixed times if any
    return [t.strip() for t in os.getenv('SCHEDULE_TIMES', '10:00,14:00,18:00').split(',')]


def run_now():
    """Run a form fill immediately (for testing)."""
    logger.info("Running immediate form fill (test mode)")
    job()


if __name__ == "__main__":
    import sys

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    if len(sys.argv) > 1 and sys.argv[1] == '--now':
        # Run immediately for testing
        run_now()
    else:
        # Run on schedule
        run_scheduler()
