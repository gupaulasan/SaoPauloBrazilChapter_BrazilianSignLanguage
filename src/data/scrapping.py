import asyncio
import os

import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "https://libras.cin.ufpe.br/"
WORDS_FILE = "v_librasil_words.txt"
PROGRESS_FILE = "v_librasil_progress.txt"


async def fetch_words(session, page):
    """Fetch words from a given page, returning an empty list if no words found."""
    url = f"{BASE_URL}?page={page}"

    try:
        async with session.get(url, timeout=30) as response:
            if response.status != 200:
                print(f"Skipping page {page}: HTTP {response.status}")
                return []

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            words = [a.text.strip() for a in soup.select("table.table tbody tr td a")]
            return words

    except aiohttp.ClientError as e:
        print(f"Request failed for page {page}: {e}")
        return []


def load_last_page():
    """Read last scraped page from progress file or start from page 1."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return int(f.read().strip())
    return 1  # Default to first page if no progress file exists


def save_last_page(page):
    """Save last successfully scraped page to progress file."""
    with open(PROGRESS_FILE, "w") as f:
        f.write(str(page))


def save_words(words):
    """Append scraped words to words file."""
    with open(WORDS_FILE, "a") as f:
        for word in words:
            f.write(word + "\n")


async def scrape_all_pages():
    """Scrape all pages dynamically until an empty page is found."""
    all_words = []
    page = load_last_page()  # Start from last saved page
    session = None

    try:
        session = aiohttp.ClientSession()
        while True:
            words = await fetch_words(session, page)
            if not words:
                print(f"No more words found. Stopping at page {page}.")
                break

            save_words(words)  # Save words immediately
            save_last_page(page)  # Save progress
            print(f"Scraped {len(words)} words from page {page}.")
            page += 1

    except asyncio.CancelledError:
        print("\nScraping process was cancelled.")

    finally:
        if session:
            await session.close()
            print("Session closed.")

    print(f"\nTotal words scraped: {len(all_words)}")
    return all_words


# Run the scraper
try:
    asyncio.run(scrape_all_pages())

except KeyboardInterrupt:
    print("\nScraping interrupted by user.")
