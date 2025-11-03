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
from scheduler import job, get_config
import schedule

# Load environment variables
load_dotenv()

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

    # Clear any existing schedules
    schedule.clear()

    # Setup schedules
    for time_str in config['schedule_times']:
        time_str = time_str.strip()
        schedule.every().day.at(time_str).do(job)
        logger.info(f"Scheduled job at {time_str}")

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

    return jsonify({
        'status': automation_status,
        'config': {
            'target_url': config['target_url'],
            'schedule_times': config['schedule_times'],
            'headless': config['headless']
        },
        'recent_logs': recent_logs
    })


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
        logger.info("Manual trigger: Starting form submission")

        config = get_config()

        # Run the form filler
        result = asyncio.run(run_single_form_fill(
            target_url=config['target_url'],
            headless=config['headless'],
            min_delay=config['min_delay'],
            max_delay=config['max_delay']
        ))

        automation_status['running'] = False
        automation_status['last_run'] = datetime.now().isoformat()
        automation_status['total_runs'] += 1

        if result:
            automation_status['successful_runs'] += 1
            automation_status['last_status'] = 'success'
            logger.info("Manual trigger: Form submission completed successfully")

            return jsonify({
                'success': True,
                'message': 'Form submission completed successfully'
            })
        else:
            automation_status['failed_runs'] += 1
            automation_status['last_status'] = 'failed'
            logger.error("Manual trigger: Form submission failed")

            return jsonify({
                'success': False,
                'message': 'Form submission failed. Check logs for details.'
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
        log_file = Path('logs/app.log')
        if not log_file.exists():
            return jsonify({'logs': []})

        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Return last 100 lines
            recent = lines[-100:] if len(lines) > 100 else lines

        return jsonify({'logs': recent})

    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({'logs': [], 'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint for Railway."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    # Create logs directory
    os.makedirs('logs', exist_ok=True)

    # Check if we should auto-start scheduler
    auto_start = os.getenv('AUTO_START_SCHEDULER', 'true').lower() == 'true'

    if auto_start:
        logger.info("Auto-starting scheduler on app startup")
        scheduler_thread = threading.Thread(target=run_scheduler_thread, daemon=True)
        scheduler_thread.start()

    # Get port from environment (Railway sets this)
    port = int(os.getenv('PORT', 5000))

    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
