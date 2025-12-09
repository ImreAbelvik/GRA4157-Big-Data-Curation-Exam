import asyncio
import json
import multiprocessing
import os
from multiprocessing import Pool

from utils import get_list_of_issuers, init_page, search_params, collect_from_table

MAIN_URL = "https://newsweb.oslobors.no/search"

async def process_issuer_async(issuer_name):
    try:
        print(f"START PROCESSING {issuer_name}")
        playwright, browser, page = await init_page(MAIN_URL, headless=True)

        page = await search_params(page, issuer=issuer_name)
    
        results = await collect_from_table(page)
    
        if results:
            # temp code to fix / after running regret _ and not just empty.
            issuer_name_path = issuer_name.replace("/", "_")

            with open(f"data/{issuer_name_path}.json", "a", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        else:
            print("No hits!")

        await page.wait_for_timeout(5000)
        await browser.close()
        await playwright.stop()

    except Exception as e:
        print(f"ATTEMPT FAIL {issuer_name}")
        os.makedirs("logs", exist_ok=True)
        with open("logs/error_list.txt", "a", encoding="utf-8") as f:
            f.write(f"ERROR WITH ISSUER: {issuer_name}\n{e}\n")


def run_process_wrapper(issuer_name):
    """
    """
    print(f"Pool worker assigned to: {issuer_name}")
    asyncio.run(process_issuer_async(issuer_name))

if __name__ == "__main__":
    issuers_list = get_list_of_issuers()

    # I did not check the file issuer_filter properly beffor scraping.
    # This resulted in trying to create a file with / in name. 
    # Luckely this is easy fix.
    # Also kinda nice knowing that its just the / betwen A/S and P/f.
    # This is so I can rename them back to original later. 
    issuers_list = [
        "5th Planet Games A/S",
        "Cadeler A/S",
        "DFDS A/S",
        "Bakkafrost P/f",
        "Napatech A/S",
        "Tryg Forsikring A/S"
    ]

    NUM_PROCESSES = 2
    with Pool(processes=NUM_PROCESSES) as pool:
        pool.map(run_process_wrapper, issuers_list)
