"""
Main entry point for the form automation tool.
"""
import asyncio
import argparse
import logging
import os
from dotenv import load_dotenv
from form_filler import run_single_form_fill
from scheduler import run_scheduler, run_now


def setup_logging():
    """Setup logging configuration."""
    os.makedirs('logs', exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/main.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """Main function."""
    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Automated form filler for noro.rs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --test          # Run once for testing (visible browser)
  python main.py --now           # Run once immediately with current settings
  python main.py --schedule      # Run on schedule (default)
  python main.py --test --headless  # Run once in headless mode
        """
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Run once for testing (default: visible browser)'
    )

    parser.add_argument(
        '--now',
        action='store_true',
        help='Run once immediately with current .env settings'
    )

    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run on schedule (reads from .env file)'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )

    parser.add_argument(
        '--url',
        type=str,
        default=os.getenv('TARGET_URL', 'https://noro.rs/'),
        help='Target URL (default: from .env or https://noro.rs/)'
    )

    args = parser.parse_args()

    # If no mode specified, default to schedule
    if not args.test and not args.now and not args.schedule:
        args.schedule = True

    try:
        if args.test:
            logger.info("Running in TEST mode")
            logger.info("This will run the form filler once with visible browser")
            logger.info("-" * 60)

            result = asyncio.run(run_single_form_fill(
                target_url=args.url,
                headless=args.headless,
                min_delay=1,
                max_delay=3,
                proxy=os.getenv('PROXY_URL', None),
                max_retries=int(os.getenv('MAX_RETRIES', '3'))
            ))

            if result:
                logger.info("Test completed successfully!")
            else:
                logger.error("Test failed!")

        elif args.now:
            logger.info("Running ONCE with current settings")
            run_now()

        elif args.schedule:
            logger.info("Running in SCHEDULE mode")
            logger.info("Form filler will run at scheduled times defined in .env")
            logger.info("-" * 60)
            run_scheduler()

    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
