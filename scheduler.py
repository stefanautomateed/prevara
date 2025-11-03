"""
Scheduler for automated form filling.
Runs form filling at specified times throughout the day.
"""
import asyncio
import logging
import os
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
from form_filler import run_single_form_fill


# Load environment variables
load_dotenv()

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


def get_config():
    """Load configuration from environment variables."""
    return {
        'target_url': os.getenv('TARGET_URL', 'https://noro.rs/'),
        'schedule_times': os.getenv('SCHEDULE_TIMES', '10:00,14:00,18:00').split(','),
        'headless': os.getenv('HEADLESS', 'false').lower() == 'true',
        'min_delay': float(os.getenv('MIN_DELAY', '1')),
        'max_delay': float(os.getenv('MAX_DELAY', '3'))
    }


def job():
    """Job to run at scheduled times."""
    logger.info("=" * 60)
    logger.info(f"Starting scheduled form fill at {datetime.now()}")
    logger.info("=" * 60)

    config = get_config()

    try:
        # Run the async form filling
        result = asyncio.run(run_single_form_fill(
            target_url=config['target_url'],
            headless=config['headless'],
            min_delay=config['min_delay'],
            max_delay=config['max_delay']
        ))

        if result:
            logger.info("Scheduled form fill completed successfully!")
        else:
            logger.error("Scheduled form fill failed!")

    except Exception as e:
        logger.error(f"Error in scheduled job: {e}")

    logger.info("=" * 60)


def setup_scheduler():
    """Setup the schedule based on configuration."""
    config = get_config()

    logger.info("Setting up scheduler...")
    logger.info(f"Target URL: {config['target_url']}")
    logger.info(f"Headless mode: {config['headless']}")
    logger.info(f"Schedule times: {config['schedule_times']}")

    # Schedule jobs for each time
    for time_str in config['schedule_times']:
        time_str = time_str.strip()
        schedule.every().day.at(time_str).do(job)
        logger.info(f"Scheduled job at {time_str}")

    logger.info("Scheduler setup complete!")
    logger.info("Waiting for scheduled times...")


def run_scheduler():
    """Run the scheduler loop."""
    setup_scheduler()

    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


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
