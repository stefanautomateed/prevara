"""
Quick test to demonstrate proxy rotation on retry.
"""
import asyncio
import logging
from form_filler import run_single_form_fill

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_rotation():
    """Test proxy rotation with multiple proxies."""
    
    # Multiple proxies - some may fail, should automatically rotate
    proxy_list = "http://139.162.78.109:8080,http://167.99.171.156:443,http://195.123.209.48:3128"
    
    print("=" * 70)
    print("🔄 TESTING PROXY ROTATION WITH RETRY")
    print("=" * 70)
    print(f"\nProxy pool: {proxy_list}")
    print("\nIf first proxy fails, it will automatically try the next one!")
    print("\n" + "=" * 70)
    
    result = await run_single_form_fill(
        target_url="https://noro.rs/",
        headless=False,  # Set to True to hide browser
        min_delay=1,
        max_delay=2,
        proxy=proxy_list,
        max_retries=3  # Will try up to 3 times with different proxies
    )
    
    print("\n" + "=" * 70)
    if result:
        print("✅ SUCCESS: Form filled successfully!")
    else:
        print("❌ FAILED: All retry attempts exhausted")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_rotation())
