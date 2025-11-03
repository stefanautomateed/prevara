"""
Web automation script for filling out forms on noro.rs
Uses Playwright for modern web automation with stealth capabilities.
"""
import asyncio
import random
import logging
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from serbian_data_generator import SerbianDataGenerator


class FormFiller:
    """Automated form filler for noro.rs website."""

    def __init__(self, target_url, headless=False, min_delay=1, max_delay=3):
        """
        Initialize the form filler.

        Args:
            target_url: URL of the target website
            headless: Run browser in headless mode
            min_delay: Minimum delay between actions (seconds)
            max_delay: Maximum delay between actions (seconds)
        """
        self.target_url = target_url
        self.headless = headless
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.logger = logging.getLogger(__name__)

    async def random_delay(self):
        """Add a random delay to simulate human behavior."""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    async def fill_form(self):
        """
        Main method to fill out the form on the website.

        Returns:
            bool: True if successful, False otherwise
        """
        profile = SerbianDataGenerator.generate_complete_profile()
        self.logger.info(f"Generated profile: {profile['name']}, {profile['phone']}")

        async with async_playwright() as p:
            try:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )

                # Create context with realistic viewport and user agent
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )

                # Create page
                page = await context.new_page()

                # Navigate to the target URL
                self.logger.info(f"Navigating to {self.target_url}")
                await page.goto(self.target_url, wait_until='networkidle', timeout=30000)
                await self.random_delay()

                # Take a screenshot for debugging (saved to logs/)
                await page.screenshot(path=f'logs/page_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')

                # NOTE: The following selectors are PLACEHOLDERS
                # You need to inspect the actual website and update these selectors
                # to match the actual form fields on noro.rs

                self.logger.info("Looking for form fields...")

                # Example: Fill name field
                # Common selectors to try: input[name="name"], #name, input[placeholder*="ime"]
                try:
                    # Try multiple possible selectors for name
                    name_selectors = [
                        'input[name="name"]',
                        'input[name="firstName"]',
                        'input[name="full_name"]',
                        'input[id="name"]',
                        'input[placeholder*="Ime"]',
                        'input[placeholder*="ime"]'
                    ]

                    for selector in name_selectors:
                        try:
                            await page.fill(selector, profile['name'], timeout=2000)
                            self.logger.info(f"Filled name field using selector: {selector}")
                            await self.random_delay()
                            break
                        except:
                            continue

                    # Try multiple possible selectors for phone
                    phone_selectors = [
                        'input[name="phone"]',
                        'input[name="telefon"]',
                        'input[type="tel"]',
                        'input[id="phone"]',
                        'input[placeholder*="Telefon"]',
                        'input[placeholder*="telefon"]'
                    ]

                    for selector in phone_selectors:
                        try:
                            await page.fill(selector, profile['phone'], timeout=2000)
                            self.logger.info(f"Filled phone field using selector: {selector}")
                            await self.random_delay()
                            break
                        except:
                            continue

                    # Try multiple possible selectors for email
                    email_selectors = [
                        'input[name="email"]',
                        'input[type="email"]',
                        'input[id="email"]',
                        'input[placeholder*="Email"]',
                        'input[placeholder*="email"]'
                    ]

                    for selector in email_selectors:
                        try:
                            await page.fill(selector, profile['email'], timeout=2000)
                            self.logger.info(f"Filled email field using selector: {selector}")
                            await self.random_delay()
                            break
                        except:
                            continue

                    # Try multiple possible selectors for address
                    address_selectors = [
                        'input[name="address"]',
                        'input[name="adresa"]',
                        'input[id="address"]',
                        'input[placeholder*="Adresa"]',
                        'input[placeholder*="adresa"]',
                        'textarea[name="address"]'
                    ]

                    for selector in address_selectors:
                        try:
                            await page.fill(selector, profile['address'], timeout=2000)
                            self.logger.info(f"Filled address field using selector: {selector}")
                            await self.random_delay()
                            break
                        except:
                            continue

                    # Try multiple possible selectors for city
                    city_selectors = [
                        'input[name="city"]',
                        'input[name="grad"]',
                        'input[id="city"]',
                        'input[placeholder*="Grad"]',
                        'input[placeholder*="grad"]',
                        'select[name="city"]'
                    ]

                    for selector in city_selectors:
                        try:
                            # Check if it's a select element
                            if 'select' in selector:
                                await page.select_option(selector, profile['city'], timeout=2000)
                            else:
                                await page.fill(selector, profile['city'], timeout=2000)
                            self.logger.info(f"Filled city field using selector: {selector}")
                            await self.random_delay()
                            break
                        except:
                            continue

                    # Try multiple possible selectors for postal code
                    postal_selectors = [
                        'input[name="postal_code"]',
                        'input[name="zip"]',
                        'input[name="postanski_broj"]',
                        'input[id="postal"]',
                        'input[placeholder*="Poštanski"]'
                    ]

                    for selector in postal_selectors:
                        try:
                            await page.fill(selector, profile['postal_code'], timeout=2000)
                            self.logger.info(f"Filled postal code field using selector: {selector}")
                            await self.random_delay()
                            break
                        except:
                            continue

                    # Look for submit button
                    submit_selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("Naruči")',
                        'button:has-text("Poruči")',
                        'button:has-text("Pošalji")',
                        'button:has-text("Dalje")',
                        'button:has-text("Nastavi")',
                        '.submit-button',
                        '#submit'
                    ]

                    # Take screenshot before submission
                    await page.screenshot(
                        path=f'logs/before_submit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                    )

                    # UNCOMMENT TO ACTUALLY SUBMIT THE FORM
                    # for selector in submit_selectors:
                    #     try:
                    #         await page.click(selector, timeout=2000)
                    #         self.logger.info(f"Clicked submit button using selector: {selector}")
                    #         await self.random_delay()
                    #         break
                    #     except:
                    #         continue

                    # Wait for navigation or success message
                    # await page.wait_for_load_state('networkidle', timeout=10000)

                    # Take screenshot after submission
                    await page.screenshot(
                        path=f'logs/after_submit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                    )

                    self.logger.info("Form filling completed successfully!")
                    self.logger.warning("NOTE: Form submission is currently DISABLED for safety")
                    self.logger.warning("Uncomment the submit section in form_filler.py to enable")

                except PlaywrightTimeout as e:
                    self.logger.error(f"Timeout while filling form: {e}")
                    await page.screenshot(
                        path=f'logs/error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                    )
                    return False

                await browser.close()
                return True

            except Exception as e:
                self.logger.error(f"Error during form filling: {e}")
                return False


async def run_single_form_fill(target_url, headless=False, min_delay=1, max_delay=3):
    """
    Run a single form fill operation.

    Args:
        target_url: URL of the target website
        headless: Run browser in headless mode
        min_delay: Minimum delay between actions
        max_delay: Maximum delay between actions

    Returns:
        bool: True if successful, False otherwise
    """
    filler = FormFiller(target_url, headless, min_delay, max_delay)
    return await filler.fill_form()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/form_filler.log'),
            logging.StreamHandler()
        ]
    )

    # Run a single test
    asyncio.run(run_single_form_fill(
        target_url="https://noro.rs/",
        headless=False,
        min_delay=1,
        max_delay=3
    ))
