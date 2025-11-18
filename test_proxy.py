"""
Test script to check if proxy servers are working.
Tests multiple proxies and shows which ones are alive.
"""
import asyncio
from playwright.async_api import async_playwright
import time

# Top proxies from the list (Elite proxies with best ping)
PROXIES_TO_TEST = [
    "http://152.26.229.52:9443",      # US - 97ms
    "http://167.99.171.156:443",      # US - 110ms
    "http://139.162.78.109:3128",     # Japan - 129ms
    "http://103.19.78.138:1111",      # Indonesia - 157ms
    "http://139.162.78.109:8080",     # Japan - 163ms
    "http://45.61.139.153:2525",      # UK - 192ms
    "http://49.144.23.208:8082",      # Philippines - 194ms
    "http://195.123.209.48:3128",     # Latvia - 196ms
    "http://36.147.78.166:443",       # China - 207ms
    "http://3.112.209.152:876",       # Japan - 215ms
]

async def test_proxy(proxy_url, test_site="http://httpbin.org/ip"):
    """Test if a single proxy works."""
    try:
        print(f"\n🔍 Testing: {proxy_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            context = await browser.new_context(
                proxy={'server': proxy_url}
            )
            
            page = await context.new_page()
            
            start_time = time.time()
            await page.goto(test_site, timeout=10000)
            elapsed = time.time() - start_time
            
            # Get the IP that the site sees
            content = await page.content()
            
            await browser.close()
            
            print(f"✅ SUCCESS: {proxy_url} ({elapsed:.2f}s)")
            print(f"   Response preview: {content[:200]}")
            return {'proxy': proxy_url, 'status': 'working', 'time': elapsed}
            
    except Exception as e:
        print(f"❌ FAILED: {proxy_url} - {str(e)[:100]}")
        return {'proxy': proxy_url, 'status': 'failed', 'error': str(e)}

async def test_all_proxies():
    """Test all proxies."""
    print("=" * 70)
    print("🧪 TESTING PROXY SERVERS")
    print("=" * 70)
    
    results = []
    for proxy in PROXIES_TO_TEST:
        result = await test_proxy(proxy)
        results.append(result)
        await asyncio.sleep(1)  # Small delay between tests
    
    print("\n" + "=" * 70)
    print("📊 RESULTS SUMMARY")
    print("=" * 70)
    
    working = [r for r in results if r['status'] == 'working']
    failed = [r for r in results if r['status'] == 'failed']
    
    print(f"\n✅ Working proxies: {len(working)}/{len(results)}")
    for r in working:
        print(f"   {r['proxy']} ({r['time']:.2f}s)")
    
    print(f"\n❌ Failed proxies: {len(failed)}/{len(results)}")
    
    if working:
        fastest = min(working, key=lambda x: x['time'])
        print(f"\n🏆 FASTEST PROXY: {fastest['proxy']} ({fastest['time']:.2f}s)")
        print(f"\n💡 Add this to your .env file:")
        print(f"   PROXY_URL={fastest['proxy']}")
    else:
        print("\n⚠️  No working proxies found. You may need to:")
        print("   1. Try again later (proxies change frequently)")
        print("   2. Get fresh proxies from https://www.proxy-list.download/HTTPS")
        print("   3. Consider a paid proxy service for reliability")

if __name__ == "__main__":
    asyncio.run(test_all_proxies())
