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

    def __init__(self, target_url, headless=False, min_delay=1, max_delay=3, use_fixed_email=False):
        """
        Initialize the form filler.

        Args:
            target_url: URL of the target website
            headless: Run browser in headless mode
            min_delay: Minimum delay between actions (seconds)
            max_delay: Maximum delay between actions (seconds)
            use_fixed_email: Use fixed email (streamentor@gmail.com) instead of random
        """
        self.target_url = target_url
        self.headless = headless
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.use_fixed_email = use_fixed_email
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
        # Generate profile with fixed email if requested
        fixed_email = "streamentor@gmail.com" if self.use_fixed_email else None
        profile = SerbianDataGenerator.generate_complete_profile(fixed_email=fixed_email)

        self.logger.info(f"Generated profile: {profile['name']}, {profile['phone']}")
        self.logger.info(f"  Email: {profile['email']}" + (" [FIXED]" if self.use_fixed_email else ""))
        self.logger.info(f"  Address: {profile['address']}")
        self.logger.info(f"  City: {profile['city']}, ZIP: {profile['postal_code']}")

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

                # Log starting URL
                self.logger.info("=" * 80)
                self.logger.info(f"📍 STARTING URL: {page.url}")
                self.logger.info("=" * 80)

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
                            # Verify the value was actually filled
                            filled_value = await page.input_value(selector)
                            self.logger.info(f"Filled name field using selector: {selector}")
                            self.logger.info(f"  ✅ Verified value: '{filled_value}'")
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
                    try:
                        await page.screenshot(
                            path=f'logs/before_submit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png',
                            full_page=True
                        )
                    except:
                        self.logger.warning("Could not take before_submit screenshot (headless mode)")

                    # CRITICAL: Verify all form data is actually filled before submitting
                    try:
                        self.logger.info("=" * 80)
                        self.logger.info("VERIFYING ALL FORM FIELDS BEFORE SUBMISSION:")
                        verification = await page.evaluate("""
                        () => {
                            const inputs = document.querySelectorAll('input, select, textarea');
                            const values = {};
                            inputs.forEach(input => {
                                if (input.name || input.id || input.placeholder) {
                                    const key = input.name || input.id || input.placeholder;
                                    values[key] = {
                                        value: input.value || '',
                                        type: input.type,
                                        required: input.required || input.hasAttribute('required'),
                                        visible: input.offsetParent !== null
                                    };
                                }
                            });
                            return values;
                        }
                        """)
                        for key, data in verification.items():
                            if data['visible'] and (data['value'] or data['required']):
                                self.logger.info(f"  {key}: '{data['value']}' (required={data['required']})")
                        self.logger.info("=" * 80)
                    except Exception as e:
                        self.logger.warning(f"Could not verify form fields: {e}")

                    # CRITICAL: Find ALL buttons on page to see what's available
                    try:
                        self.logger.info("=" * 80)
                        self.logger.info("FINDING ALL BUTTONS ON PAGE:")
                        all_buttons_info = await page.evaluate("""
                        () => {
                            const buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"], a[role="button"]');
                            return Array.from(buttons).map((btn, index) => ({
                                index: index + 1,
                                text: btn.textContent.trim() || btn.value || '',
                                type: btn.type || btn.tagName,
                                id: btn.id || '',
                                className: btn.className || '',
                                visible: btn.offsetParent !== null,
                                disabled: btn.disabled || false
                            }));
                        }
                        """)
                        for btn in all_buttons_info[:15]:  # Show first 15
                            if btn['visible']:
                                self.logger.info(f"  Button {btn['index']}: '{btn['text']}' (type={btn['type']}, disabled={btn['disabled']})")
                        self.logger.info("=" * 80)
                    except Exception as e:
                        self.logger.warning(f"Could not enumerate buttons: {e}")

                    # SUBMIT THE FORM - Try standard selectors first
                    submit_clicked = False
                    for selector in submit_selectors:
                        try:
                            count = await page.locator(selector).count()
                            if count > 0:
                                # Check what the button actually does
                                button_info = await page.evaluate(f"""
                                () => {{
                                    const btn = document.querySelector('{selector}');
                                    if (!btn) return null;
                                    return {{
                                        type: btn.type,
                                        form: btn.form ? {{
                                            action: btn.form.action,
                                            method: btn.form.method,
                                            hasSubmit: true
                                        }} : null,
                                        onclick: btn.onclick ? 'has onclick' : 'no onclick',
                                        disabled: btn.disabled
                                    }};
                                }}
                                """)
                                if button_info:
                                    self.logger.info(f"Button '{selector}' info: {button_info}")

                                await page.click(selector, timeout=2000)
                                self.logger.info(f"✅ Clicked submit button using selector: {selector}")
                                submit_clicked = True
                                await self.random_delay()
                                break
                        except Exception as e:
                            self.logger.debug(f"Selector {selector} failed: {e}")
                            continue

                    # FALLBACK: Try to find button by partial text match
                    if not submit_clicked:
                        try:
                            self.logger.warning("Standard selectors failed, trying JavaScript search for 'Naruči' button...")
                            js_find_submit = """
                            () => {
                                const buttons = document.querySelectorAll('button, input[type="submit"]');
                                for (let btn of buttons) {
                                    const text = (btn.textContent || btn.value || '').toLowerCase();
                                    if (text.includes('naruči') || text.includes('naruci') || text.includes('poruč')) {
                                        btn.click();
                                        return {found: true, text: btn.textContent || btn.value};
                                    }
                                }
                                return {found: false};
                            }
                            """
                            result = await page.evaluate(js_find_submit)
                            if result.get('found'):
                                self.logger.info(f"✅ Found and clicked submit button via JS: '{result.get('text')}'")
                                submit_clicked = True
                                await self.random_delay()
                            else:
                                self.logger.error("❌ Could not find any submit button with 'Naruči' text!")
                        except Exception as e:
                            self.logger.error(f"JavaScript button search failed: {e}")

                    if submit_clicked:
                        # Wait for navigation or success message
                        try:
                            await page.wait_for_load_state('networkidle', timeout=10000)
                            self.logger.info("Page loaded after submission")

                            # Log URL immediately after submission
                            url_after_submit = page.url
                            self.logger.info(f"📍 URL after form submit: {url_after_submit}")

                        except:
                            self.logger.warning("Timeout waiting for page load, continuing...")
                            # Still log URL even if timeout
                            try:
                                url_after_submit = page.url
                                self.logger.info(f"📍 URL after form submit (timeout): {url_after_submit}")
                            except:
                                pass

                        # CRITICAL: Wait for navigation or processing after submit
                        self.logger.info("=" * 80)
                        self.logger.info("⏳ Waiting for order processing/navigation...")
                        self.logger.info("=" * 80)

                        try:
                            # Wait for navigation to complete (e.g., to thank-you page)
                            # Use wait_for_load_state with a reasonable timeout
                            await page.wait_for_load_state('networkidle', timeout=8000)
                            self.logger.info("✅ Network idle detected")
                        except:
                            self.logger.info("⚠️ Network idle timeout (page might still be processing)")

                        # Give additional time for any redirects or JavaScript
                        await asyncio.sleep(2)

                        # Check current URL after waiting
                        current_url = page.url
                        self.logger.info(f"📍 Current URL after waiting: {current_url}")

                        # Check if we successfully navigated to thank-you/success page
                        if 'thank-you' in current_url or 'success' in current_url or 'potvrda' in current_url:
                            self.logger.info("=" * 80)
                            self.logger.info(f"✅ SUCCESS! Navigated to: {current_url}")
                            self.logger.info("=" * 80)
                        # If URL didn't change, try alternatives
                        elif current_url == self.target_url or 'noro.rs/' == current_url.rstrip('/').split('/')[-1]:
                            self.logger.warning(f"⚠️ URL didn't change from starting page: {current_url}")
                            self.logger.warning("This suggests the form submission didn't work properly")

                            # Check ALL visible buttons to understand what options we have
                            self.logger.info("=" * 80)
                            self.logger.info("🔍 ANALYZING ALL VISIBLE BUTTONS ON PAGE:")
                            all_buttons = await page.evaluate("""
                            () => {
                                const buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"]');
                                return Array.from(buttons)
                                    .filter(btn => btn.offsetParent !== null)  // Only visible
                                    .map(btn => ({
                                        text: (btn.textContent || btn.value || '').trim(),
                                        type: btn.type || btn.tagName,
                                        id: btn.id,
                                        className: btn.className,
                                        disabled: btn.disabled
                                    }));
                            }
                            """)

                            for i, btn in enumerate(all_buttons[:10], 1):
                                self.logger.info(f"  Button {i}: '{btn['text']}' (disabled={btn['disabled']})")
                            self.logger.info("=" * 80)

                            # Check for error messages or validation failures
                            error_check = await page.evaluate("""
                            () => {
                                const errorSelectors = [
                                    '.error', '.alert-danger', '[class*="error"]',
                                    '[class*="invalid"]', '[role="alert"]'
                                ];
                                for (let sel of errorSelectors) {
                                    const elem = document.querySelector(sel);
                                    if (elem && elem.offsetParent !== null) {
                                        return {found: true, text: elem.textContent.substring(0, 200)};
                                    }
                                }
                                return {found: false};
                            }
                            """)

                            if error_check.get('found'):
                                self.logger.error(f"❌ ERROR MESSAGE DETECTED: {error_check.get('text')}")

                            # DON'T automatically click any confirmation dialogs
                            # Instead, try alternative submission method
                            self.logger.warning("Attempting alternative: Direct form.submit() call...")
                            try:
                                submit_result = await page.evaluate("""
                                () => {
                                    const form = document.querySelector('form');
                                    if (form) {
                                        form.submit();
                                        return {success: true, action: form.action};
                                    }
                                    return {success: false};
                                }
                                """)

                                if submit_result.get('success'):
                                    self.logger.info(f"✅ Called form.submit() - action: {submit_result.get('action')}")
                                    await asyncio.sleep(3)

                                    final_url = page.url
                                    self.logger.info(f"📍 URL after form.submit(): {final_url}")

                                    if 'thank-you' in final_url:
                                        self.logger.info("✅ SUCCESS via form.submit()!")
                            except Exception as e:
                                self.logger.error(f"form.submit() failed: {e}")

                            # Final check after all attempts
                            final_check_url = page.url
                            if final_check_url == self.target_url or final_check_url.rstrip('/') == self.target_url.rstrip('/'):
                                self.logger.error("=" * 80)
                                self.logger.error("❌ SUBMISSION FAILED - URL did not change")
                                self.logger.error(f"Still at: {final_check_url}")
                                self.logger.error("=" * 80)
                    # Take screenshot after submission
                    try:
                        await page.screenshot(
                            path=f'logs/after_submit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                        )
                    except:
                        self.logger.warning("Could not take after_submit screenshot (headless mode)")

                    # Track final URL after all processing
                    try:
                        final_url = page.url
                        self.logger.info("=" * 80)
                        self.logger.info(f"🎯 FINAL URL AFTER ORDERING: {final_url}")
                        self.logger.info("=" * 80)

                        # Check if we're on a success/thank-you page
                        page_content = await page.content()
                        success_keywords = ['hvala', 'thank', 'success', 'uspešno', 'potvrda', 'confirmation', 'order', 'porudžbina']

                        found_keywords = [kw for kw in success_keywords if kw in page_content.lower()]
                        if found_keywords:
                            self.logger.info(f"✅ Success page detected (keywords: {', '.join(found_keywords)})")
                        else:
                            self.logger.warning("⚠️ Not sure if order was successful - no success keywords found")

                        # Log page title for context
                        try:
                            page_title = await page.title()
                            self.logger.info(f"📄 Page title: {page_title}")
                        except:
                            pass

                    except Exception as e:
                        self.logger.warning(f"Could not track final URL: {e}")

                    if submit_clicked:
                        self.logger.info("Form submission completed successfully!")
                    else:
                        self.logger.warning("Could not find submit button - form filled but not submitted")

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


async def run_single_form_fill(target_url, headless=False, min_delay=1, max_delay=3, use_fixed_email=False):
    """
    Run a single form fill operation.

    Args:
        target_url: URL of the target website
        headless: Run browser in headless mode
        min_delay: Minimum delay between actions
        max_delay: Maximum delay between actions
        use_fixed_email: Use fixed email (streamentor@gmail.com) instead of random

    Returns:
        bool: True if successful, False otherwise
    """
    filler = FormFiller(target_url, headless, min_delay, max_delay, use_fixed_email)
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
