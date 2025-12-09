def get_list_of_issuers() -> list:
    with open("issuer_filter.txt", "r", encoding="utf-8") as f:
        my_list = []
        for line in f.readlines():
            line = line.strip()
            if "kommune" in line.lower():
                continue
            else:
                my_list.append(line)

        return my_list


from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError
import asyncio
async def init_page(url, headless=True):
    
    max_retries = 2

    for attempt in range(max_retries):
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=headless, args=["--no-sandbox"])
    
            page = await browser.new_page()

            await page.goto(url)
            await page.wait_for_load_state("networkidle")

            return playwright, browser, page
        except:
            if attempt + 1 == max_retries:
                raise

            await asyncio.sleep(3)


async def search_params(page, issuer):
    advanced_options = page.locator("span:has-text('Show advanced search')")
    await advanced_options.click()

    target_text = "MANDATORY NOTIFICATION OF TRADE PRIMARY INSIDERS"
    
    input_box_category = page.locator("#react-select-7-input")
    await input_box_category.fill(target_text)
    await page.keyboard.press("Enter")


    await page.fill('input[name="fromDate"]', "01.01.2015")
    await page.fill('input[name="toDate"]', "30.10.2025")
    await page.keyboard.press('Enter')
    
    input_box_issuer = page.locator("#react-select-11-input")
    await input_box_issuer.fill(issuer)
    await page.keyboard.press("Enter")

    # Stuborn ass page wont load with the setting!
    await page.wait_for_timeout(1000)
    await page.locator('button:has-text("SEARCH")').first.click(force=True)
    await page.wait_for_timeout(1000)
    await page.locator('button:has-text("SEARCH")').first.click(force=True)
    
    return page


async def collect_from_table(page):
    results = []

    while True:
        try:
            await page.wait_for_selector("main tbody tr", timeout=5000)
        except:
            return False
        

        rows = await page.query_selector_all("main tbody tr")

        for row in rows:
            try:
                tds = await row.query_selector_all("td")
        
                row_data = {}
            
                row_data["date"] = await tds[0].inner_text()
                row_data["market"] = await tds[1].inner_text()
                row_data["IssuerID"] = await tds[2].inner_text()

                row_data["message"] = await tds[3].inner_text()
                link_elem = await tds[3].query_selector("a")
                link = await link_elem.get_attribute("href") if link_elem else None
                row_data["link"] = link

                # Its a img... but ok
                corr_elem = await tds[4].query_selector("img")
                if corr_elem:
                    corr = await corr_elem.get_attribute("alt")
                else:
                    corr = None

                row_data["Corr"] = corr

                row_data["Attach"] = await tds[5].inner_text()
                row_data["Category"] = await tds[6].inner_text()

                results.append(row_data)
            
            except:
                print("error collection row data")
        
        #Check if page has ul.pagination
        pagination = page.locator("ul.pagination")
        try:
            await pagination.wait_for(state="visible", timeout=2000)
            exists = True
        except TimeoutError:
            exists = False

        if exists:
            next_button = page.locator("ul.pagination li:has(a:has-text('⟩'))")
            await next_button.scroll_into_view_if_needed()
            if await next_button.count() == 0:
                break

            classes = await next_button.get_attribute("class") or ""
            if "disabled" in classes:
                break

            next_link = next_button.locator("a")
            await next_link.scroll_into_view_if_needed()
            await next_link.click()
            await page.wait_for_load_state("networkidle")
        else:
            return results

    return results
