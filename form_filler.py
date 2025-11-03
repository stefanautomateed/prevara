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
                    try:
                        await page.screenshot(
                            path=f'logs/before_submit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                        )
                    except:
                        self.logger.warning("Could not take before_submit screenshot (headless mode)")

                    # SUBMIT THE FORM
                    submit_clicked = False
                    for selector in submit_selectors:
                        try:
                            await page.click(selector, timeout=2000)
                            self.logger.info(f"Clicked submit button using selector: {selector}")
                            submit_clicked = True
                            await self.random_delay()
                            break
                        except:
                            continue

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

                        # Handle any confirmation dialogs/popups
                        try:
                            # Look for common confirmation buttons
                            confirmation_selectors = [
                                'button:has-text("OK")',
                                'button:has-text("Potvrdi")',
                                'button:has-text("Da")',
                                'button:has-text("Accept")',
                                'button:has-text("Prihvati")',
                                'button:has-text("Close")',
                                'button:has-text("Zatvori")',
                                '.modal button',
                                '.confirmation button'
                            ]

                            for selector in confirmation_selectors:
                                try:
                                    # Check if button exists
                                    if await page.locator(selector).count() > 0:
                                        await page.click(selector, timeout=2000)
                                        self.logger.info(f"Clicked confirmation button: {selector}")
                                        await self.random_delay()
                                        break
                                except:
                                    continue

                        except Exception as e:
                            self.logger.info(f"No confirmation dialog found or handled: {e}")

                        # CRITICAL: Select product package BEFORE clicking "Potvrdi porudžbinu"
                        # This is required for limitlesss.rs checkout flow
                        try:
                            self.logger.info("Looking for product package selection buttons...")
                            await asyncio.sleep(2)  # Wait for page to stabilize

                            # Common package selection button patterns
                            package_selectors = [
                                'button:has-text("Optimalna")',  # "Optimalna ušteda" package
                                'button:has-text("ušteda")',
                                'button:has-text("Start")',      # "Start paket"
                                'button:has-text("paket")',
                                'button:has-text("All-in")',     # "All-in paket"
                                '[class*="package"]:has-text("paket")',
                                '[class*="product"]:has-text("paket")',
                                'button[type="button"]:has-text("paket")',
                            ]

                            package_found = False
                            for selector in package_selectors:
                                try:
                                    count = await page.locator(selector).count()
                                    if count > 0:
                                        # Get button text to verify it's a package button
                                        btn_text = await page.locator(selector).first.inner_text()
                                        self.logger.info(f"🎯 Found package button: '{btn_text.strip()}'")

                                        # Scroll into view
                                        await page.locator(selector).first.scroll_into_view_if_needed(timeout=2000)
                                        await asyncio.sleep(0.5)

                                        # Click the package button
                                        await page.click(selector, timeout=5000)
                                        self.logger.info(f"✅ Clicked package button: '{btn_text.strip()}'")
                                        package_found = True

                                        # Wait for page to update after package selection
                                        await asyncio.sleep(2)
                                        self.logger.info("Waiting for page to update after package selection...")

                                        break
                                except Exception as e:
                                    if "timeout" not in str(e).lower():
                                        self.logger.debug(f"Could not check package selector {selector}: {e}")
                                    continue

                            if package_found:
                                self.logger.info("✅ Package selected - proceeding to checkout confirmation")
                            else:
                                self.logger.warning("⚠️ No package selection button found (might not be needed for this site)")

                        except Exception as e:
                            self.logger.info(f"Package selection error (might not be needed): {e}")

                        # NEW: Click final "Potvrdi porudžbinu" button (for limitlesss.rs checkout)
                        try:
                            self.logger.info("Looking for final order confirmation button...")
                            await asyncio.sleep(2)  # Wait for page to stabilize

                            final_confirmation_selectors = [
                                'button:has-text("Potvrdi porudžbinu")',  # Main button
                                'button:has-text("Potvrdi")',  # Generic
                                '[class*="checkout"]:has-text("Potvrdi")',
                                '[class*="confirm"]:has-text("Potvrdi")',
                                'button[type="submit"]:has-text("Potvrdi")',
                            ]

                            final_button_found = False
                            for selector in final_confirmation_selectors:
                                try:
                                    count = await page.locator(selector).count()
                                    if count > 0:
                                        # Get button text to verify it's the right one
                                        btn_text = await page.locator(selector).first.inner_text()
                                        if "porudžbinu" in btn_text.lower() or "rsd" in btn_text.lower():
                                            self.logger.info(f"🎯 Found final confirmation button: '{btn_text.strip()}'")

                                            # Get current URL before clicking
                                            url_before = page.url
                                            self.logger.info(f"URL before click: {url_before}")

                                            # INSPECT button properties first
                                            try:
                                                safe_sel = selector.replace("'", "\\'")
                                                # Use function form to avoid f-string issues
                                                js_inspect = """
                                                (selector) => {
                                                    const btn = document.querySelector(selector);
                                                    if (!btn) return null;
                                                    return {
                                                        tagName: btn.tagName,
                                                        type: btn.type,
                                                        className: btn.className,
                                                        id: btn.id,
                                                        disabled: btn.disabled,
                                                        hasOnClick: !!btn.onclick,
                                                        hasForm: !!btn.form,
                                                        dataAttributes: Array.from(btn.attributes)
                                                            .filter(attr => attr.name.startsWith('data-'))
                                                            .map(attr => attr.name + '=' + attr.value)
                                                    };
                                                }
                                                """
                                                button_info = await page.evaluate(js_inspect, safe_sel)
                                                self.logger.info(f"🔍 Button inspection: {button_info}")
                                            except Exception as e:
                                                self.logger.warning(f"Could not inspect button: {e}")

                                            # Scroll into view
                                            await page.locator(selector).first.scroll_into_view_if_needed(timeout=2000)
                                            await asyncio.sleep(1)

                                            # CAPTURE network requests to see what gets sent
                                            captured_requests = []

                                            def capture_request(request):
                                                if request.method in ['POST', 'PUT', 'PATCH']:
                                                    captured_requests.append({
                                                        'url': request.url,
                                                        'method': request.method,
                                                        'post_data': request.post_data
                                                    })

                                            page.on('request', capture_request)
                                            self.logger.info("Started capturing network requests...")

                                            # Try multiple approaches to click/submit
                                            click_success = False

                                            # APPROACH 1: Direct HTTP POST (bypass UI completely)
                                            try:
                                                self.logger.info("Approach 1: Direct HTTP POST request...")

                                                # Extract form data and action URL
                                                js_extract_form = """
                                                () => {
                                                    const forms = document.querySelectorAll('form');
                                                    for (let form of forms) {
                                                        const submitBtn = form.querySelector('button[type="submit"]');
                                                        if (submitBtn && submitBtn.textContent.includes('Potvrdi')) {
                                                            const formData = {};
                                                            const inputs = form.querySelectorAll('input, select, textarea');
                                                            inputs.forEach(input => {
                                                                if (input.name) {
                                                                    formData[input.name] = input.value || '';
                                                                }
                                                            });
                                                            return {
                                                                action: form.action || window.location.href,
                                                                method: form.method || 'POST',
                                                                data: formData
                                                            };
                                                        }
                                                    }
                                                    return null;
                                                }
                                                """
                                                form_info = await page.evaluate(js_extract_form)

                                                if form_info:
                                                    self.logger.info(f"Form action: {form_info['action']}")
                                                    self.logger.info(f"Form method: {form_info['method']}")
                                                    self.logger.info(f"Form data keys: {list(form_info['data'].keys())}")

                                                    # Send POST request using Playwright's request context
                                                    response = await page.request.post(
                                                        form_info['action'],
                                                        data=form_info['data'],
                                                        headers={
                                                            'Content-Type': 'application/x-www-form-urlencoded',
                                                            'Referer': page.url
                                                        }
                                                    )

                                                    self.logger.info(f"POST response status: {response.status}")

                                                    if response.ok:
                                                        self.logger.info("✅ HTTP POST successful!")
                                                        # Reload page to see result
                                                        await page.reload()
                                                        await asyncio.sleep(2)
                                                        click_success = True
                                                    else:
                                                        self.logger.warning(f"POST failed with status {response.status}")
                                                else:
                                                    self.logger.info("Could not extract form info for POST")

                                            except Exception as e:
                                                self.logger.warning(f"HTTP POST approach failed: {e}")

                                            # APPROACH 2: JavaScript click on button
                                            if not click_success:
                                                try:
                                                    self.logger.info("Approach 2: JavaScript click on button...")
                                                    safe_selector = selector.replace("'", "\\'")
                                                    js_click = """
                                                    (sel) => {
                                                        const btn = document.querySelector(sel);
                                                        if (btn) {
                                                            btn.click();
                                                            return true;
                                                        }
                                                        return false;
                                                    }
                                                    """
                                                    result = await page.evaluate(js_click, safe_selector)
                                                    if result:
                                                        self.logger.info("✅ Clicked via JavaScript")
                                                        click_success = True
                                                except Exception as e:
                                                    self.logger.warning(f"JS click failed: {e}")

                                            # APPROACH 3: Dispatch mouse events (most realistic)
                                            if not click_success:
                                                try:
                                                    self.logger.info("Approach 3: Dispatching mouse events...")
                                                    safe_selector = selector.replace("'", "\\'")
                                                    js_events = """
                                                    (sel) => {
                                                        const btn = document.querySelector(sel);
                                                        if (btn) {
                                                            btn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
                                                            btn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
                                                            btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                                                            return true;
                                                        }
                                                        return false;
                                                    }
                                                    """
                                                    event_result = await page.evaluate(js_events, safe_selector)
                                                    if event_result:
                                                        self.logger.info("✅ Mouse events dispatched")
                                                        click_success = True
                                                except Exception as e:
                                                    self.logger.warning(f"Mouse event dispatch failed: {e}")

                                            # APPROACH 4: Playwright click with force (last resort)
                                            if not click_success:
                                                try:
                                                    self.logger.info("Approach 4: Playwright force click...")
                                                    await page.click(selector, timeout=5000, force=True)
                                                    self.logger.info("✅ Clicked via Playwright")
                                                    click_success = True
                                                except Exception as e:
                                                    self.logger.error(f"All 4 click approaches failed: {e}")

                                            final_button_found = True

                                            # Stop capturing and log what we found
                                            try:
                                                page.remove_listener('request', capture_request)
                                            except:
                                                pass

                                            # Log captured requests
                                            if captured_requests:
                                                self.logger.info(f"🔍 Captured {len(captured_requests)} POST/PUT/PATCH requests:")
                                                for req in captured_requests:
                                                    self.logger.info(f"  → {req['method']} {req['url']}")
                                                    if req['post_data']:
                                                        self.logger.info(f"    Data: {req['post_data'][:200]}")  # First 200 chars
                                            else:
                                                self.logger.warning("⚠️ NO POST requests captured - form might use different submission method!")

                                            # Wait for popup/modal to appear (user said it's on same page!)
                                            self.logger.info("Waiting for order bump popup/modal to appear...")

                                            # Wait for modal/popup with specific text
                                            popup_appeared = False
                                            for wait_attempt in range(10):  # Try for 10 seconds
                                                try:
                                                    # Check if popup with "Ne, hvala (nastavi)" appeared
                                                    js_check_popup = """
                                                    () => {
                                                        const body = document.body.textContent || '';
                                                        return body.includes('Ne, hvala') || body.includes('nastavi') || body.includes('Čestitamo');
                                                    }
                                                    """
                                                    has_popup = await page.evaluate(js_check_popup)

                                                    if has_popup:
                                                        self.logger.info(f"✅ Order bump popup appeared after {wait_attempt + 1} seconds!")
                                                        popup_appeared = True
                                                        break

                                                    await asyncio.sleep(1)
                                                except:
                                                    await asyncio.sleep(1)

                                            if not popup_appeared:
                                                self.logger.warning("⚠️ Order bump popup did NOT appear after clicking!")
                                                # Check if we're still on checkout page
                                                still_has_button = await page.locator(selector).count() > 0
                                                if still_has_button:
                                                    self.logger.error("❌ Button is STILL there - click FAILED completely!")
                                                else:
                                                    self.logger.info("Button disappeared but no popup - might have progressed")

                                            break
                                except Exception as e:
                                    if "timeout" not in str(e).lower():
                                        self.logger.debug(f"Could not check selector {selector}: {e}")
                                    continue

                            if not final_button_found:
                                self.logger.info("No final 'Potvrdi porudžbinu' button found (might already be past checkout)")

                        except Exception as e:
                            self.logger.info(f"Final confirmation check error: {e}")

                        # Handle order bump / upsell popups (especially for limitlesss.rs)
                        try:
                            self.logger.info("Looking for order bump/upsell offers...")

                            # Give MORE time for the popup to appear (5 seconds instead of random 1-3)
                            self.logger.info("Waiting 5 seconds for order bump popup to load...")
                            await asyncio.sleep(5)

                            # Scroll to bottom of page to ensure popup is loaded and visible
                            try:
                                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                                self.logger.info("Scrolled to bottom of page")
                                await asyncio.sleep(1)
                                # Scroll back to middle
                                await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                                self.logger.info("Scrolled to middle of page")
                                await asyncio.sleep(1)
                            except:
                                pass

                            # Take screenshot to see what's on the page
                            try:
                                await page.screenshot(
                                    path=f'logs/order_bump_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png',
                                    full_page=True
                                )
                                self.logger.info("Full page screenshot taken for order bump investigation")
                            except:
                                pass

                            # Log all buttons on the page for debugging
                            try:
                                all_buttons = await page.locator('button, a[role="button"], input[type="submit"], input[type="button"]').all()
                                self.logger.info(f"Total buttons found on page: {len(all_buttons)}")
                                for i, btn in enumerate(all_buttons[:20]):  # Log first 20 buttons
                                    try:
                                        text = await btn.inner_text()
                                        self.logger.info(f"Button {i+1}: '{text.strip()}'")
                                    except:
                                        pass
                            except Exception as e:
                                self.logger.warning(f"Could not enumerate buttons: {e}")

                            # Look for order bump reject/decline buttons with more variations
                            order_bump_reject_selectors = [
                                # Exact text matches (case-insensitive)
                                'button:has-text("Ne, hvala (nastavi)")',
                                'a:has-text("Ne, hvala (nastavi)")',
                                'button:has-text("Ne, hvala")',
                                'a:has-text("Ne, hvala")',

                                # Partial matches
                                'button:has-text("nastavi")',
                                'a:has-text("nastavi")',
                                'button:has-text("hvala")',
                                'a:has-text("hvala")',

                                # Common variations
                                'button:has-text("Ne hvala")',
                                'button:has-text("Odbij")',
                                'button:has-text("Decline")',
                                'button:has-text("No thanks")',
                                'button:has-text("Skip")',
                                'button:has-text("Preskoči")',
                                'button:has-text("Zatvori")',
                                'button:has-text("Close")',

                                # Links
                                'a:has-text("Ne hvala")',
                                'a:has-text("Odbij")',

                                # By class/id
                                '[class*="decline"]',
                                '[class*="reject"]',
                                '[class*="skip"]',
                                '[class*="no-thanks"]',
                                '[id*="decline"]',
                                '[id*="reject"]',

                                # Generic "close" or "continue" selectors
                                'button.close',
                                'button.skip',
                                'a.close',
                                'a.skip',

                                # By text content (any element)
                                '*:has-text("Ne, hvala (nastavi)")',
                                '*:has-text("nastavi")'
                            ]

                            order_bump_found = False
                            for selector in order_bump_reject_selectors:
                                try:
                                    # Check if order bump button exists
                                    count = await page.locator(selector).count()
                                    if count > 0:
                                        self.logger.info(f"🎯 FOUND order bump button! Selector: {selector}, Count: {count}")

                                        # Try to scroll element into view first
                                        try:
                                            element = page.locator(selector).first
                                            await element.scroll_into_view_if_needed(timeout=2000)
                                            self.logger.info("Scrolled element into view")
                                        except:
                                            pass

                                        # Try to click
                                        await page.click(selector, timeout=3000, force=True)
                                        self.logger.info(f"✅ Clicked order bump REJECT button: {selector}")
                                        order_bump_found = True
                                        await self.random_delay()

                                        # Wait for any final navigation
                                        try:
                                            await page.wait_for_load_state('networkidle', timeout=5000)
                                            self.logger.info("Page loaded after order bump decline")
                                        except:
                                            pass

                                        break
                                except Exception as e:
                                    # Log errors for debugging
                                    if "timeout" not in str(e).lower():
                                        self.logger.debug(f"Could not click {selector}: {e}")
                                    continue

                            if not order_bump_found:
                                self.logger.warning("⚠️ NO order bump button found! Checking page...")
                                # Log current URL to help debug
                                current_url = page.url
                                self.logger.info(f"Current URL: {current_url}")

                                # Try to get page title
                                try:
                                    title = await page.title()
                                    self.logger.info(f"Page title: {title}")
                                except:
                                    pass

                                # Get page HTML for debugging
                                try:
                                    html_content = await page.content()
                                    # Log if we find any text containing "nastavi" or "hvala"
                                    if "nastavi" in html_content.lower() or "hvala" in html_content.lower():
                                        self.logger.info("⚠️ Found 'nastavi' or 'hvala' in page HTML but couldn't match selector!")
                                        # Save HTML for inspection
                                        with open(f'logs/order_bump_html_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html', 'w', encoding='utf-8') as f:
                                            f.write(html_content)
                                        self.logger.info("Saved page HTML to logs/ for inspection")
                                except Exception as e:
                                    self.logger.warning(f"Could not check page HTML: {e}")

                        except Exception as e:
                            self.logger.info(f"Order bump handling error (likely no order bump present): {e}")

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
