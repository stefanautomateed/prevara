"""
Flask web application for form automation tool.
Provides web interface to manually trigger form submissions and view logs.
"""
import asyncio
import os
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import logging
from pathlib import Path

from form_filler import run_single_form_fill
from scheduler import job, get_config, setup_scheduler, get_current_schedule_times
from stats import (
    load_stats,
    increment_manual_trigger,
    increment_submission_attempts,
    increment_successes,
    increment_failures
)
import schedule

# Load environment variables
load_dotenv()

# Ensure logs directory exists before configuring file handlers
os.makedirs('logs', exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Global state
automation_status = {
    'running': False,
    'last_run': None,
    'last_status': None,
    'total_runs': 0,
    'successful_runs': 0,
    'failed_runs': 0,
    'scheduler_active': False
}

scheduler_thread = None


def run_scheduler_thread():
    """Run the scheduler in a background thread."""
    config = get_config()

    # Delegate to central scheduler setup (handles random/fixed modes)
    setup_scheduler()

    automation_status['scheduler_active'] = True

    # Run scheduler loop
    while automation_status['scheduler_active']:
        schedule.run_pending()
        time.sleep(60)


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current automation status."""
    config = get_config()

    # Get recent logs
    recent_logs = []
    log_file = Path('logs/app.log')
    if log_file.exists():
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_logs = lines[-50:]  # Last 50 lines

    payload = {
        'status': automation_status,
        'config': {
            'target_urls': config['target_urls'],
            'schedule_times': get_current_schedule_times(),
            'headless': config['headless'],
            'random_schedule': config.get('random_schedule', False),
            'runs_per_day': config.get('runs_per_day', None),
            'time_window_start': config.get('time_window_start', None),
            'time_window_end': config.get('time_window_end', None),
            'min_gap_minutes': config.get('min_gap_minutes', None)
        },
        'recent_logs': recent_logs,
        'stats': load_stats()
    }
    return jsonify(payload)


@app.route('/api/run', methods=['POST'])
def trigger_run():
    """Manually trigger a form submission."""
    if automation_status['running']:
        return jsonify({
            'success': False,
            'message': 'A form submission is already in progress'
        }), 400

    try:
        automation_status['running'] = True
        logger.info("Manual trigger: Starting form submission for all URLs")

        # Get use_fixed_email parameter from request
        use_fixed_email = False
        if request.is_json:
            data = request.get_json()
            use_fixed_email = data.get('use_fixed_email', False)
            logger.info(f"Using fixed email: {use_fixed_email}")

        config = get_config()

        # Count manual trigger once
        try:
            increment_manual_trigger()
        except Exception as e:
            logger.warning(f"Could not persist manual trigger stat: {e}")

        # Run the form filler for all URLs
        all_success = True
        results = []

        for target_url in config['target_urls']:
            try:
                logger.info(f"Manual trigger: Processing {target_url}")

                result = asyncio.run(run_single_form_fill(
                    target_url=target_url,
                    headless=config['headless'],
                    min_delay=config['min_delay'],
                    max_delay=config['max_delay'],
                    use_fixed_email=use_fixed_email
                ))

                automation_status['total_runs'] += 1
                try:
                    increment_submission_attempts(1)
                except Exception:
                    pass

                if result:
                    automation_status['successful_runs'] += 1
                    try:
                        increment_successes(1)
                    except Exception:
                        pass
                    results.append(f"✅ {target_url}")
                    logger.info(f"Manual trigger: {target_url} completed successfully")
                else:
                    automation_status['failed_runs'] += 1
                    all_success = False
                    try:
                        increment_failures(1)
                    except Exception:
                        pass
                    results.append(f"❌ {target_url}")
                    logger.error(f"Manual trigger: {target_url} failed")

            except Exception as e:
                automation_status['failed_runs'] += 1
                automation_status['total_runs'] += 1
                try:
                    increment_submission_attempts(1)
                    increment_failures(1)
                except Exception:
                    pass
                all_success = False
                results.append(f"❌ {target_url} (error)")
                logger.error(f"Manual trigger error for {target_url}: {e}")

        automation_status['running'] = False
        automation_status['last_run'] = datetime.now().isoformat()
        automation_status['last_status'] = 'success' if all_success else 'partial' if len(results) > 0 else 'failed'

        result_message = '\n'.join(results)

        if all_success:
            return jsonify({
                'success': True,
                'message': f'All form submissions completed successfully!\n{result_message}'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Some submissions failed:\n{result_message}'
            }), 500

    except Exception as e:
        automation_status['running'] = False
        automation_status['failed_runs'] += 1
        automation_status['last_status'] = 'error'
        logger.error(f"Manual trigger error: {e}")

        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the scheduler."""
    global scheduler_thread

    if automation_status['scheduler_active']:
        return jsonify({
            'success': False,
            'message': 'Scheduler is already running'
        }), 400

    try:
        scheduler_thread = threading.Thread(target=run_scheduler_thread, daemon=True)
        scheduler_thread.start()

        logger.info("Scheduler started via web interface")

        return jsonify({
            'success': True,
            'message': 'Scheduler started successfully'
        })

    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the scheduler."""
    if not automation_status['scheduler_active']:
        return jsonify({
            'success': False,
            'message': 'Scheduler is not running'
        }), 400

    try:
        automation_status['scheduler_active'] = False
        schedule.clear()

        logger.info("Scheduler stopped via web interface")

        return jsonify({
            'success': True,
            'message': 'Scheduler stopped successfully'
        })

    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/logs')
def get_logs():
    """Get recent logs."""
    try:
        # Collect logs from all log files
        all_logs = []

        # Try app.log
        app_log = Path('logs/app.log')
        if app_log.exists():
            with open(app_log, 'r') as f:
                all_logs.extend(f.readlines())

        # Try form_filler.log
        form_log = Path('logs/form_filler.log')
        if form_log.exists():
            with open(form_log, 'r') as f:
                all_logs.extend(f.readlines())

        # Try scheduler.log
        scheduler_log = Path('logs/scheduler.log')
        if scheduler_log.exists():
            with open(scheduler_log, 'r') as f:
                all_logs.extend(f.readlines())

        # If no logs found, return empty
        if not all_logs:
            return jsonify({'logs': ['No logs available yet. Logs will appear after first run.']})

        # Sort by timestamp and return last 100 lines
        recent = all_logs[-100:] if len(all_logs) > 100 else all_logs

        return jsonify({'logs': recent})

    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({'logs': [f'Error reading logs: {str(e)}'], 'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint for Railway."""
    return jsonify({'status': 'healthy'}), 200


def init_app():
    """Initialize the application."""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)

    # Check if we should auto-start scheduler
    auto_start = os.getenv('AUTO_START_SCHEDULER', 'true').lower() == 'true'

    if auto_start:
        logger.info("Auto-starting scheduler on app startup")
        global scheduler_thread
        scheduler_thread = threading.Thread(target=run_scheduler_thread, daemon=True)
        scheduler_thread.start()

    logger.info("Application initialized successfully")


# Initialize app when loaded (for gunicorn)
init_app()


if __name__ == '__main__':
    # Get port from environment (Railway sets this)
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting Flask development server on port {port}")

    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
