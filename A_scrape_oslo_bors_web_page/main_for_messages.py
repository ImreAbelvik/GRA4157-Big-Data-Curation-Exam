import asyncio
from playwright.async_api import async_playwright, Page
import os
import json
import time
import random

MAIN_URL = "https://newsweb.oslobors.no"
DATA_PATH = "data"
SAVE_DATA_PATH = "data_"
CONCURRENT_LIMIT = 6


# DONE
def get_meta_data(file):
    file_path = os.path.join(DATA_PATH, file)
    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    
    issuer_id = json_data[0].get("IssuerID")
    message_id = [item["link"].lstrip("/").replace("/", "_") for item in json_data if "link" in item]
    urls = [MAIN_URL + item["link"] for item in json_data if "link" in item]

    return issuer_id, message_id, urls


async def scrape_page(context, url, semaphore, save_dir):
    """
    Scrapes a single page and saves downloaded files under save_dir.
    """
    async with semaphore:
        page = await context.new_page()

        delay = min(random.expovariate(1/1), 9)
        await asyncio.sleep(delay)

        try:
            await page.goto(url, wait_until="load", timeout=60000)


            attachment_links_locator = page.locator("xpath=//span[text()='Attachment']/following::ul[1]//a")
            
            count = 0
            try:
                # 2. Wait for the *first* attachment link to be visible.
                # This ensures the JavaScript has loaded the attachment section.
                # If this times out, it means no attachments were found.
                await attachment_links_locator.first.wait_for(state="visible", timeout=10000) # 10-second timeout
                count = await attachment_links_locator.count()
                #print(f"Found {count} attachments for {url}")

            except:
                #print(f"Found 0 attachments for {url} (section did not appear).")
                count = 0
            
            for i in range(count):
                link = attachment_links_locator.nth(i)
                
                try:
                    async with page.expect_download(timeout=60000) as download_info:
                        await link.click()
                    
                    download = await download_info.value
                    file_path = os.path.join(save_dir, download.suggested_filename)
                    await download.save_as(file_path)
                    #print(f"Successfully saved: {file_path}")
                except Exception as e:
                    pass
            # --- End of updated logic ---

            body = await page.locator("div[role='document']").text_content()

            document_text_file = os.path.join(save_dir, "document_text.txt") 
            with open(document_text_file, "w", encoding="utf-8") as f:
                f.write(str(body))
            
            contentinfo_divs = await page.query_selector_all('div[role="contentinfo"]')
            for div in contentinfo_divs:
                corrected_span = await div.query_selector('span:has-text("Corrected versions")')
                show_next_span = await div.query_selector('span:has-text("Show next version")')
                if corrected_span and show_next_span:
                    file_path = os.path.join(save_dir, "error")
                    with open(file_path, "w") as f:
                        pass

        finally:
            await page.close()


async def main_scraper(urls_to_scrape, issuer_save_path, message_ids):
    semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)

        tasks = []
        for url, msg_id in zip(urls_to_scrape, message_ids):
            save_dir = os.path.join(issuer_save_path, str(msg_id))
            os.makedirs(save_dir, exist_ok=True)
            tasks.append(scrape_page(context, url, semaphore, save_dir))

        await asyncio.gather(*tasks)
        await browser.close()


import time
def main():
    data = os.listdir(DATA_PATH)
    data = [item for i, item in enumerate(data) if i != 3]

    len_data = len(data)
    count_scraped = 0
    print(f"Scraping data for {len_data} issuers")

    for file in data:
        issuer_id, message_id, urls = get_meta_data(file)


        issuer_save_path = os.path.join(SAVE_DATA_PATH, issuer_id)
        if os.path.exists(issuer_save_path):
            print(f"Folder for issuer {issuer_id} already exists. Exiting loop.")
            continue
        else:
            os.makedirs(issuer_save_path, exist_ok=True)
            #time.sleep(2)

        print(f"Scraping data for {issuer_id} issuer has {len(urls)} urls to scrape.")
        print(f"This is number {count_scraped} issuer scraped.")

        asyncio.run(main_scraper(urls, issuer_save_path, message_id))

        count_scraped += 1


if __name__ == "__main__":
    main()
    
