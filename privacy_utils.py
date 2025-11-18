"""
Privacy and anonymity utilities for web automation.
Provides user agent rotation, viewport randomization, and log cleanup.
"""
import random
import os
import time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PrivacyUtils:
    """Utilities for enhancing privacy and avoiding detection."""

    # Realistic User Agents (recent browsers, common configurations)
    USER_AGENTS = [
        # Chrome on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        
        # Chrome on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        
        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        
        # Firefox on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        
        # Edge on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        
        # Safari on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    ]

    # Common viewport resolutions (width, height)
    VIEWPORTS = [
        {'width': 1920, 'height': 1080},  # Full HD
        {'width': 1366, 'height': 768},   # Common laptop
        {'width': 1536, 'height': 864},   # Scaled laptop
        {'width': 1440, 'height': 900},   # MacBook Pro 13"
        {'width': 1680, 'height': 1050},  # Common desktop
        {'width': 2560, 'height': 1440},  # 2K
        {'width': 1600, 'height': 900},   # HD+
        {'width': 1280, 'height': 720},   # HD
    ]

    @staticmethod
    def get_random_user_agent():
        """
        Get a random realistic User Agent string.
        
        Returns:
            str: Random User Agent
        """
        return random.choice(PrivacyUtils.USER_AGENTS)

    @staticmethod
    def get_random_viewport():
        """
        Get a random viewport resolution.
        
        Returns:
            dict: Dictionary with 'width' and 'height'
        """
        return random.choice(PrivacyUtils.VIEWPORTS).copy()

    @staticmethod
    def get_locale_and_timezone():
        """
        Get random but realistic locale and timezone for Serbian user.
        
        Returns:
            tuple: (locale, timezone_id)
        """
        # Most common for Serbian users
        locales = ['sr-RS', 'sr-Latn-RS', 'en-US']
        timezones = ['Europe/Belgrade']
        
        return random.choice(locales), random.choice(timezones)

    @staticmethod
    def cleanup_old_files(directory='logs', max_age_hours=24, file_extensions=None):
        """
        Delete files older than max_age_hours from the specified directory.
        
        Args:
            directory: Directory to clean
            max_age_hours: Maximum file age in hours
            file_extensions: List of extensions to delete (e.g., ['.har', '.png', '.log'])
                           If None, deletes all files
        """
        if not os.path.exists(directory):
            return

        cutoff_time = time.time() - (max_age_hours * 3600)
        deleted_count = 0

        try:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                
                # Skip if not a file
                if not os.path.isfile(filepath):
                    continue
                
                # Check extension filter
                if file_extensions:
                    if not any(filename.endswith(ext) for ext in file_extensions):
                        continue
                
                # Check file age
                file_mtime = os.path.getmtime(filepath)
                if file_mtime < cutoff_time:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        logger.info(f"Deleted old file: {filename}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {filename}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old file(s) from {directory}/")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    @staticmethod
    def add_random_jitter(base_time_str, max_jitter_minutes=15):
        """
        Add random time jitter to a scheduled time.
        
        Args:
            base_time_str: Time string in HH:MM format
            max_jitter_minutes: Maximum jitter in minutes (both directions)
        
        Returns:
            str: New time in HH:MM format
        """
        try:
            hours, minutes = map(int, base_time_str.split(':'))
            total_minutes = hours * 60 + minutes
            
            # Add random jitter
            jitter = random.randint(-max_jitter_minutes, max_jitter_minutes)
            new_total = total_minutes + jitter
            
            # Handle day wrap
            new_total = new_total % (24 * 60)
            
            new_hours = new_total // 60
            new_minutes = new_total % 60
            
            return f"{new_hours:02d}:{new_minutes:02d}"
        except Exception as e:
            logger.warning(f"Failed to add jitter to {base_time_str}: {e}")
            return base_time_str

    @staticmethod
    def parse_proxy_string(proxy_str):
        """
        Parse proxy string into Playwright-compatible format.
        
        Supported formats:
        - http://proxy.com:8080
        - http://user:pass@proxy.com:8080
        - socks5://proxy.com:1080
        
        Args:
            proxy_str: Proxy URL string
        
        Returns:
            dict: Playwright proxy configuration or None
        """
        if not proxy_str or proxy_str.strip() == '':
            return None
        
        try:
            # Basic parsing (could be enhanced)
            proxy_config = {'server': proxy_str}
            
            # Extract username/password if present
            if '@' in proxy_str:
                # Format: protocol://user:pass@host:port
                parts = proxy_str.split('@')
                if len(parts) == 2:
                    auth_part = parts[0].split('//')[-1]  # user:pass
                    if ':' in auth_part:
                        username, password = auth_part.split(':', 1)
                        proxy_config['username'] = username
                        proxy_config['password'] = password
                        # Rebuild server without credentials
                        protocol = proxy_str.split('://')[0]
                        proxy_config['server'] = f"{protocol}://{parts[1]}"
            
            logger.info(f"Parsed proxy: {proxy_config['server']}")
            return proxy_config
        except Exception as e:
            logger.error(f"Failed to parse proxy string '{proxy_str}': {e}")
            return None

    @staticmethod
    def get_random_delays(base_min=1.0, base_max=3.0, variance=0.5):
        """
        Get random delay values with variance.
        
        Args:
            base_min: Base minimum delay
            base_max: Base maximum delay
            variance: Random variance to apply
        
        Returns:
            tuple: (min_delay, max_delay)
        """
        min_delay = base_min + random.uniform(-variance, variance)
        max_delay = base_max + random.uniform(-variance, variance)
        
        # Ensure min < max and both are positive
        min_delay = max(0.5, min_delay)
        max_delay = max(min_delay + 0.5, max_delay)
        
        return round(min_delay, 2), round(max_delay, 2)
