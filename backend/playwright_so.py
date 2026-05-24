import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        print("Logging in...")
        await page.goto("https://systematic.ominfo.in/erp/index.php")
        await page.fill("input[name='emailid']", "SYS079")
        await page.fill("input[name='psw']", "5651")
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")

        print("Navigating to SO detail...")
        
        # Intercept network requests
        api_responses = {}
        async def handle_response(response):
            if "php" in response.url and response.request.resource_type in ["xhr", "fetch"]:
                try:
                    text = await response.text()
                    api_responses[response.url] = text[:500]
                except:
                    pass
        
        page.on("response", handle_response)
        
        await page.goto("https://systematic.ominfo.in/erp/crm_sales_order_manage.php?function=2&orderno=4305")
        
        # Wait for table to populate
        try:
            await page.wait_for_selector("#dataTable_body tr", timeout=5000)
            print("Table populated!")
        except:
            print("Table not populated or timed out")
            
        rows = await page.locator("#dataTable_body tr").all()
        for i, r in enumerate(rows):
            text = await r.inner_text()
            print(f"Row {i}: {text.replace(chr(10), ' | ')}")
            
        print("\nAPI Calls made:")
        for url, text in api_responses.items():
            print(f"URL: {url}")
            print(f"Response: {text}\n")
            
        await browser.close()

asyncio.run(main())
