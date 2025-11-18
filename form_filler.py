"""
Web automation script for filling out forms on noro.rs
Uses Playwright for modern web automation with stealth capabilities.
"""
import asyncio
import random
import logging
from datetime import datetime
import re
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from serbian_data_generator import SerbianDataGenerator
from privacy_utils import PrivacyUtils


class FormFiller:
    """Automated form filler for noro.rs website."""

    def __init__(self, target_url, headless=False, min_delay=1, max_delay=3, proxy=None):
        """
        Initialize the form filler.

        Args:
            target_url: URL of the target website
            headless: Run browser in headless mode
            min_delay: Minimum delay between actions (seconds)
            max_delay: Maximum delay between actions (seconds)
            proxy: Proxy server URL (e.g., 'http://proxy.com:8080' or 'socks5://user:pass@proxy.com:1080')
        """
        self.target_url = target_url
        self.headless = headless
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.proxy = PrivacyUtils.parse_proxy_string(proxy) if proxy else None
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
        # Generate random profile (always use random email for privacy)
        profile = SerbianDataGenerator.generate_complete_profile()

        self.logger.info(f"Generated profile: {profile['name']}, {profile['phone']}")
        self.logger.info(f"  Email: {profile['email']}")
        self.logger.info(f"  Address: {profile['address']}")
        self.logger.info(f"  City: {profile['city']}, ZIP: {profile['postal_code']}")

        async with async_playwright() as p:
            try:
                # Ensure logs directory exists for traces/HAR/screenshots
                os.makedirs('logs', exist_ok=True)
                
                # Clean up old files before starting (older than 24 hours)
                PrivacyUtils.cleanup_old_files('logs', max_age_hours=24, file_extensions=['.har', '.png', '.zip'])
                
                # Launch browser
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )

                # Get randomized privacy settings
                user_agent = PrivacyUtils.get_random_user_agent()
                viewport = PrivacyUtils.get_random_viewport()
                locale, timezone = PrivacyUtils.get_locale_and_timezone()
                
                self.logger.info(f"Privacy settings: UA={user_agent[:50]}..., Viewport={viewport}, Proxy={'Yes' if self.proxy else 'No'}")
                
                # Create context with randomized settings
                context_options = {
                    'viewport': viewport,
                    'user_agent': user_agent,
                    'locale': locale,
                    'timezone_id': timezone,
                    'record_har_path': f'logs/session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.har',
                    'record_har_omit_content': False
                }
                
                # Add proxy if configured
                if self.proxy:
                    context_options['proxy'] = self.proxy
                    self.logger.info(f"Using proxy: {self.proxy['server']}")
                
                context = await browser.new_context(**context_options)

                # Basic stealth tweaks
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    Object.defineProperty(navigator, 'languages', { get: () => ['sr-RS', 'sr', 'en-US'] });
                    Object.defineProperty(navigator, 'platform', { get: () => 'MacIntel' });
                    window.chrome = window.chrome || { runtime: {} };
                """)

                # Start tracing
                try:
                    await context.tracing.start(screenshots=True, snapshots=True, sources=True)
                except Exception:
                    pass

                # Create page
                page = await context.new_page()

                # Attach verbose listeners
                try:
                    page.on("console", lambda m: self.logger.info(f"CONSOLE [{m.type}] {m.text}"))
                    page.on("request", lambda r: self.logger.info(f"REQUEST {r.method} {r.url}"))
                    page.on("response", lambda r: self.logger.info(f"RESPONSE {r.status} {r.url}"))
                except Exception:
                    pass

                # Navigate to the target URL
                self.logger.info(f"Navigating to {self.target_url}")
                await page.goto(self.target_url, wait_until='networkidle', timeout=30000)
                try:
                    await page.wait_for_selector('form, input, button', timeout=10000)
                except Exception:
                    pass
                await self.random_delay()

                # Human-like interactions: slight scrolls and delays
                try:
                    for y in [300, 800, 1200]:
                        await page.mouse.wheel(0, y)
                        await asyncio.sleep(0.3)
                    await page.mouse.move(200, 200)
                    await asyncio.sleep(0.2)
                    await page.mouse.move(400, 350)
                    await asyncio.sleep(0.2)
                except Exception:
                    pass

                # Log starting URL
                self.logger.info("=" * 80)
                self.logger.info(f"📍 STARTING URL: {page.url}")
                self.logger.info("=" * 80)

                # Take a screenshot for debugging (saved to logs/)
                await page.screenshot(path=f'logs/page_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')

                # Try to accept cookie consent if present
                try:
                    consent_selectors = [
                        'button:has-text("Prihvati")',
                        'button:has-text("Prihvatam")',
                        'button:has-text("Slažem")',
                        'button:has-text("Slažem se")',
                        'button:has-text("Accept")',
                        '#onetrust-accept-btn-handler',
                        'button[aria-label*="Accept"]'
                    ]
                    for sel in consent_selectors:
                        try:
                            if await page.locator(sel).first.is_visible():
                                await page.locator(sel).first.click(timeout=1000)
                                self.logger.info(f"Dismissed cookie banner via selector: {sel}")
                                await self.random_delay()
                                break
                        except Exception:
                            continue
                except Exception:
                    pass

                # If this is a WooCommerce shop, follow the standard cart/checkout flow
                try:
                    body_classes = await page.evaluate("document.body.className")
                except Exception:
                    body_classes = ""

                if 'woocommerce' in body_classes or await page.locator('.woocommerce, .add_to_cart_button, .single_add_to_cart_button').first.count() > 0:
                    self.logger.info("Detected WooCommerce storefront — executing cart/checkout flow")

                    # Ensure we are on a product page; if not, try to open the first product
                    try:
                        # If product add button exists on current page, use it; else navigate to first product
                        add_btn = page.locator('.single_add_to_cart_button, .add_to_cart_button').first
                        if not await add_btn.count():
                            # Try to click first product card
                            product_link = page.locator('.products .product a.woocommerce-LoopProduct-link').first
                            if await product_link.count():
                                await product_link.click()
                                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                                await self.random_delay()
                            else:
                                # Fallback paths commonly used in WooCommerce
                                for path in ['/shop/', '/prodavnica/']:
                                    try:
                                        await page.goto(self.target_url.rstrip('/') + path, timeout=10000)
                                        await page.wait_for_load_state('domcontentloaded', timeout=10000)
                                        product_link = page.locator('.products .product a.woocommerce-LoopProduct-link').first
                                        if await product_link.count():
                                            await product_link.click()
                                            await page.wait_for_load_state('domcontentloaded', timeout=10000)
                                            await self.random_delay()
                                            break
                                    except Exception:
                                        continue

                        # Click add to cart
                        add_btn = page.locator('.single_add_to_cart_button, .add_to_cart_button').first
                        if await add_btn.count():
                            await add_btn.click()
                            self.logger.info("Clicked Add to Cart")
                            await self.random_delay()
                        else:
                            self.logger.warning("No add-to-cart button found; continuing with generic flow")
                    except Exception as e:
                        self.logger.warning(f"WooCommerce add-to-cart step failed: {e}")

                    # Go to cart
                    try:
                        # Prefer direct cart link if present
                        cart_link = page.locator('a[href*="/cart" i], a:has-text("Korpa"), a:has-text("Cart")').first
                        if await cart_link.count():
                            await cart_link.click()
                        else:
                            await page.goto(self.target_url.rstrip('/') + '/cart/', timeout=10000)
                        await page.wait_for_load_state('domcontentloaded', timeout=10000)
                        self.logger.info(f"At cart: {page.url}")
                        await self.random_delay()
                    except Exception as e:
                        self.logger.warning(f"Cart navigation failed: {e}")

                    # Proceed to checkout
                    try:
                        checkout_btn = page.locator('.checkout-button, a[href*="/checkout" i], a:has-text("Plaćanje"), a:has-text("Checkout")').first
                        if await checkout_btn.count():
                            await checkout_btn.click()
                        else:
                            await page.goto(self.target_url.rstrip('/') + '/checkout/', timeout=10000)
                        await page.wait_for_load_state('domcontentloaded', timeout=15000)
                        self.logger.info(f"At checkout: {page.url}")
                        await self.random_delay()
                    except Exception as e:
                        self.logger.warning(f"Checkout navigation failed: {e}")

                    # Fill WooCommerce billing fields
                    try:
                        # Split name into first/last
                        parts = profile['name'].split()
                        first_name = parts[0]
                        last_name = parts[-1] if len(parts) > 1 else 'Kupac'

                        mapping = [
                            ('#billing_first_name, [name="billing_first_name"]', first_name),
                            ('#billing_last_name, [name="billing_last_name"]', last_name),
                            ('#billing_phone, [name="billing_phone"]', profile['phone']),
                            ('#billing_address_1, [name="billing_address_1"]', profile['address']),
                            ('#billing_city, [name="billing_city"]', profile['city']),
                            ('#billing_postcode, [name="billing_postcode"]', profile['postal_code']),
                            ('#billing_email, [name="billing_email"]', profile['email'])
                        ]

                        for selector, value in mapping:
                            try:
                                locator = page.locator(selector).first
                                if await locator.count():
                                    await locator.fill(str(value))
                                    self.logger.info(f"Filled {selector} = {value}")
                                    await self.random_delay()
                            except Exception:
                                continue

                        # Accept terms if required
                        try:
                            terms = page.locator('#terms, [name="terms"]').first
                            if await terms.count():
                                state = await terms.is_checked()
                                if not state:
                                    await terms.check()
                                    self.logger.info("Checked terms checkbox")
                        except Exception:
                            pass

                        # Place order
                        place = page.locator('#place_order, button[name="woocommerce_checkout_place_order"], button:has-text("Poruči"), button:has-text("Naruči")').first
                        if await place.count():
                            await place.click()
                            self.logger.info("Clicked Place Order")
                            await self.random_delay()
                        else:
                            self.logger.warning("Place order button not found on checkout")
                    except Exception as e:
                        self.logger.warning(f"Checkout filling failed: {e}")

                    # After placing order, let the generic thank-you detection handle success

                # Attempt to click a CTA that opens the order form
                try:
                    cta_selectors = [
                        'a:has-text("Poruči")',
                        'button:has-text("Poruči")',
                        'a:has-text("Naruči")',
                        'button:has-text("Naruči")',
                        'a:has-text("Kupi")',
                        'button:has-text("Kupi")',
                        'a:has-text("Poruč")',
                        'button:has-text("Poruč")'
                    ]
                    clicked_cta = False
                    for sel in cta_selectors:
                        try:
                            if await page.locator(sel).first.is_visible():
                                await page.locator(sel).first.click(timeout=2000)
                                self.logger.info(f"Clicked CTA to open form: {sel}")
                                clicked_cta = True
                                await self.random_delay()
                                break
                        except Exception:
                            continue

                    if clicked_cta:
                        # Wait a bit for modal/iframe to appear
                        await asyncio.sleep(1.5)
                except Exception:
                    pass

                # Determine the DOM context that actually contains the form (page or iframe)
                dom = page
                try:
                    has_form_on_page = await page.locator('form').count() > 0
                    if not has_form_on_page:
                        for frame in page.frames:
                            try:
                                if await frame.locator('form').count() > 0:
                                    dom = frame
                                    self.logger.info(f"Detected form inside iframe: {frame.url}")
                                    break
                            except Exception:
                                continue
                except Exception:
                    dom = page

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
                            await dom.fill(selector, profile['name'], timeout=2000)
                            # Verify the value was actually filled
                            filled_value = await dom.input_value(selector)
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
                            await dom.fill(selector, profile['phone'], timeout=2000)
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
                            await dom.fill(selector, profile['email'], timeout=2000)
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
                            await dom.fill(selector, profile['address'], timeout=2000)
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
                                await dom.select_option(selector, profile['city'], timeout=2000)
                            else:
                                await dom.fill(selector, profile['city'], timeout=2000)
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
                            await dom.fill(selector, profile['postal_code'], timeout=2000)
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

                    # Before submission: try to auto-select required radios/selects and check consent boxes
                    try:
                        self.logger.info("Pre-submission: auto-selecting radios/selects and checking consents...")
                        await dom.evaluate("""
                        () => {
                            // Helper: click first visible element
                            const clickVisible = (el) => {
                                if (!el) return false;
                                const rect = el.getBoundingClientRect();
                                const visible = rect.width > 0 && rect.height > 0;
                                if (visible) { el.click(); return true; }
                                return false;
                            };

                            // 1) Check consent/terms checkboxes
                            const consentLabels = ['uslov', 'prihvat', 'saglas', 'policy', 'pravila', 'terms'];
                            document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                                const text = (cb.getAttribute('name') || '') + ' ' + (cb.id || '');
                                const label = document.querySelector(`label[for="${cb.id}"]`);
                                const labelText = (label ? label.textContent : '') || '';
                                const match = consentLabels.some(k => labelText.toLowerCase().includes(k) || text.toLowerCase().includes(k));
                                const visible = cb.offsetParent !== null;
                                if (visible && match && !cb.checked) cb.click();
                            });

                            // 2) Pick first option for required radio groups
                            const radios = Array.from(document.querySelectorAll('input[type="radio"]'))
                                .filter(r => r.offsetParent !== null);
                            const groups = new Map();
                            radios.forEach(r => {
                                const n = r.name || '__anon__';
                                if (!groups.has(n)) groups.set(n, []);
                                groups.get(n).push(r);
                            });
                            const likelyChoiceNames = ['pak', 'paket', 'option', 'opcija', 'vel', 'velicina', 'size', 'kolic', 'koli'];
                            groups.forEach((arr, name) => {
                                const required = arr.some(r => r.required || r.hasAttribute('required')) ||
                                    likelyChoiceNames.some(k => (name||'').toLowerCase().includes(k));
                                if (required) {
                                    const first = arr.find(r => r.offsetParent !== null);
                                    if (first && !first.checked) first.click();
                                }
                            });

                            // 3) For visible required selects, choose the first non-empty option
                            document.querySelectorAll('select[required]').forEach(sel => {
                                if (sel.offsetParent !== null) {
                                    const opt = Array.from(sel.options).find(o => o.value && o.value !== '');
                                    if (opt) sel.value = opt.value;
                                }
                            });
                        }
                        """)
                    except Exception as e:
                        self.logger.warning(f"Pre-submission auto-select failed: {e}")

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

                    # CRITICAL: Select product quantity BEFORE submitting (noro.rs specific)
                    # Buttons 6, 7, 8 are quantity selectors (0, 1, 2 packages)
                    # Button 9 is "Primeni" (Apply) button
                    try:
                        self.logger.info("=" * 80)
                        self.logger.info("🔢 SELECTING PRODUCT QUANTITY...")

                        # Find and click quantity button "1" or "2" (not "0")
                        quantity_result = await page.evaluate("""
                        () => {
                            const buttons = document.querySelectorAll('button');
                            for (let btn of buttons) {
                                const text = (btn.textContent || '').trim();
                                // Find button with just "1" or "2" as text (quantity buttons)
                                if ((text === '1' || text === '2') && btn.type === 'button') {
                                    btn.click();
                                    return {success: true, quantity: text, buttonType: btn.type};
                                }
                            }
                            return {success: false};
                        }
                        """)

                        if quantity_result.get('success'):
                            self.logger.info(f"✅ Selected quantity: {quantity_result.get('quantity')} package(s)")
                            await asyncio.sleep(1)

                            # Now click "Primeni" (Apply) button
                            primeni_result = await page.evaluate("""
                            () => {
                                const buttons = document.querySelectorAll('button');
                                for (let btn of buttons) {
                                    const text = (btn.textContent || '').trim().toLowerCase();
                                    if (text === 'primeni') {
                                        btn.click();
                                        return {success: true};
                                    }
                                }
                                return {success: false};
                            }
                            """)

                            if primeni_result.get('success'):
                                self.logger.info("✅ Clicked 'Primeni' (Apply) button")
                                await asyncio.sleep(2)  # Wait for form to update
                                self.logger.info("Waiting for form to update after quantity selection...")
                            else:
                                self.logger.warning("⚠️ Could not find 'Primeni' button")
                        else:
                            self.logger.info("ℹ️ No quantity selector buttons found (might not be needed for this site)")

                        self.logger.info("=" * 80)
                    except Exception as e:
                        self.logger.warning(f"Quantity selection not applicable: {e}")

                    # SUBMIT THE FORM - Try standard selectors first
                    submit_clicked = False
                    for selector in submit_selectors:
                        try:
                            count = await dom.locator(selector).count()
                            if count > 0:
                                # Check what the button actually does
                                button_info = await dom.evaluate(f"""
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

                                await dom.click(selector, timeout=2000)
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
                                    if (text.includes('naruči') || text.includes('naruci') || text.includes('poruč') || text.includes('završi naručivanje') || text.includes('zavrsi narucivanje')) {
                                        btn.click();
                                        return {found: true, text: btn.textContent || btn.value};
                                    }
                                }
                                return {found: false};
                            }
                            """
                            result = await dom.evaluate(js_find_submit)
                            if result.get('found'):
                                self.logger.info(f"✅ Found and clicked submit button via JS: '{result.get('text')}'")
                                submit_clicked = True
                                await self.random_delay()
                            else:
                                self.logger.error("❌ Could not find any submit button with 'Naruči' text!")
                        except Exception as e:
                            self.logger.error(f"JavaScript button search failed: {e}")

                    # If still not clicked, try dispatching the form's submit event (triggers JS handlers)
                    if not submit_clicked:
                        try:
                            dispatched = await dom.evaluate("""
                            () => {
                                const form = document.querySelector('form');
                                if (!form) return {ok: false, reason: 'no form'};
                                const ev = new Event('submit', { bubbles: true, cancelable: true });
                                return { ok: form.dispatchEvent(ev) };
                            }
                            """)
                            if dispatched and dispatched.get('ok'):
                                self.logger.info("Dispatched form submit event")
                                submit_clicked = True
                                await self.random_delay()
                        except Exception as e:
                            self.logger.warning(f"Dispatch submit failed: {e}")

                    submission_success = False

                    if submit_clicked:
                        # Track pages before potential popup
                        pages_before = len(context.pages)

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

                        # Check for a new popup/tab that might contain thank-you
                        try:
                            popup = await page.wait_for_event('popup', timeout=4000)
                            if popup:
                                self.logger.info("Detected popup after submit; switching to it")
                                page = popup
                                await page.wait_for_load_state('load', timeout=10000)
                        except Exception:
                            pass

                        # Fallback: if original page closed or a new page appeared, switch to newest
                        try:
                            if len(context.pages) > pages_before:
                                page = context.pages[-1]
                                self.logger.info("Switched to newest page after submit")
                        except Exception:
                            pass

                        # CRITICAL: Wait for navigation or processing after submit
                        self.logger.info("=" * 80)
                        self.logger.info("⏳ Waiting for order processing/navigation...")
                        self.logger.info("=" * 80)

                        try:
                            # Prefer explicit URL change to a thank-you-like page
                            await page.wait_for_url(re.compile(r'(thank|hvala|potvr|uspe|success)', re.I), timeout=10000)
                            self.logger.info("✅ Thank-you URL pattern detected")
                        except Exception:
                            try:
                                await page.wait_for_load_state('networkidle', timeout=8000)
                                self.logger.info("✅ Network idle detected")
                            except Exception:
                                self.logger.info("⚠️ Network idle timeout (page might still be processing)")

                        # Give additional time for any redirects or JavaScript
                        await asyncio.sleep(2)

                        # Check current URL after waiting
                        current_url = page.url
                        self.logger.info(f"📍 Current URL after waiting: {current_url}")

                        # Check if we successfully navigated to thank-you/success page
                        thankyou_url_markers = ['thank-you', 'success', 'potvr', 'hvala', 'order-received', 'order', 'primlj', 'uspe']
                        if any(marker in current_url.lower() for marker in thankyou_url_markers):
                            self.logger.info("=" * 80)
                            self.logger.info(f"✅ SUCCESS! Navigated to: {current_url}")
                            self.logger.info("=" * 80)
                            submission_success = True
                        # If URL didn't change, try alternatives
                        elif current_url.rstrip('/') == self.target_url.rstrip('/'):
                            self.logger.warning(f"⚠️ URL didn't change from starting page: {current_url}")
                            self.logger.warning("This suggests the form submission didn't work properly")

                            # Check ALL visible buttons to understand what options we have
                            self.logger.info("=" * 80)
                            self.logger.info("🔍 ANALYZING ALL VISIBLE BUTTONS ON PAGE:")
                            all_buttons = await dom.evaluate("""
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
                            error_check = await dom.evaluate("""
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

                            # Inspect invalid fields via HTML5 validity API
                            try:
                                invalid = await dom.evaluate("""
                                () => Array.from(document.querySelectorAll('input, select, textarea'))
                                    .filter(el => el.matches(':invalid'))
                                    .map(el => ({ name: el.name||el.id||el.placeholder||el.tagName, type: el.type||el.tagName }))
                                """)
                                if invalid and len(invalid) > 0:
                                    self.logger.warning(f"Invalid fields detected: {invalid}")
                            except Exception as e:
                                self.logger.debug(f"Invalid field inspection failed: {e}")

                            # DON'T automatically click any confirmation dialogs
                            # Instead, try alternative submission method
                            self.logger.warning("Attempting alternative: Direct form.submit() call...")
                            try:
                                submit_result = await dom.evaluate("""
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

                                    if any(marker in final_url.lower() for marker in thankyou_url_markers):
                                        self.logger.info("✅ SUCCESS via form.submit()!")
                                        submission_success = True
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

                    # Track final URL after all processing and content markers
                    try:
                        final_url = page.url
                        self.logger.info("=" * 80)
                        self.logger.info(f"🎯 FINAL URL AFTER ORDERING: {final_url}")
                        self.logger.info("=" * 80)

                        # Check if we're on a success/thank-you page by content
                        page_text = (await page.content()).lower()
                        success_keywords = [
                            'hvala', 'zahval', 'thank', 'success', 'uspešno', 'uspesno', 'potvrda', 'confirmation',
                            'porudžb', 'porudzb', 'narudžb', 'narudzb', 'primljena', 'primili smo', 'vaša porudžbina', 'vasa porudzbina',
                            'order received', 'woocommerce-order', 'woocommerce-thankyou', 'order-received'
                        ]
                        if any(kw in page_text for kw in success_keywords):
                            self.logger.info("✅ Success page detected by content keywords")
                            submission_success = True
                        else:
                            # Try DOM markers quickly
                            try:
                                has_wc = await page.locator('.woocommerce-order, .woocommerce-thankyou-order-received, .order-received').count() > 0
                                if has_wc:
                                    self.logger.info("✅ Success page detected by WooCommerce markers")
                                    submission_success = True
                            except Exception:
                                pass

                        # Log page title for context
                        try:
                            page_title = await page.title()
                            self.logger.info(f"📄 Page title: {page_title}")
                        except Exception:
                            pass

                    except Exception as e:
                        self.logger.warning(f"Could not track final URL: {e}")

                    if not submit_clicked:
                        self.logger.warning("Could not find submit button - form filled but not submitted")

                except PlaywrightTimeout as e:
                    self.logger.error(f"Timeout while filling form: {e}")
                    await page.screenshot(
                        path=f'logs/error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                    )
                    return False

                # Stop tracing and close
                try:
                    await context.tracing.stop(path='logs/trace.zip')
                except Exception:
                    pass

                await browser.close()
                return submission_success

            except Exception as e:
                self.logger.error(f"Error during form filling: {e}")
                return False


async def run_single_form_fill(target_url, headless=False, min_delay=1, max_delay=3, proxy=None):
    """
    Run a single form fill operation.

    Args:
        target_url: URL of the target website
        headless: Run browser in headless mode
        min_delay: Minimum delay between actions
        max_delay: Maximum delay between actions
        proxy: Proxy server URL (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    filler = FormFiller(target_url, headless, min_delay, max_delay, proxy)
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
