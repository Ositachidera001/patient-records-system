"""
news_scraper.py

Web-scraping module for the patient system (Lesson 21A).

WHAT THIS FILE DOES
----------------------
Scrapes practice/demo sites (NOT real medical news sites -- these are
scraping-education sandboxes built for learning) and pulls out content
that's relevant to a health-system context:

  1. quotes.toscrape.com -> quotes whose TAGS mention science, medicine,
     or health (used for the "Latest health headlines" menu option).
  2. books.toscrape.com   -> books whose TITLE mentions health, medicine,
     or nursing (BONUS -- shown alongside the quotes on the same menu).

IMPORTANT HONESTY NOTE ABOUT THE DATA
----------------------------------------
quotes.toscrape.com is a small, fixed demo dataset (~100 quotes across
10 pages) built for practicing scraping technique -- it is NOT a curated
health-news source, and it may genuinely have zero quotes tagged
"science", "medicine", or "health" at any given time depending on the
site's current content. That's expected and NOT a bug: the filtering
logic below is written to handle "found nothing that matches" cleanly
(returns an empty list, never crashes), exactly the same way it would
handle "found five matches". Don't assume an empty result means broken
code -- check the site's actual tags if you want to confirm.

WHY EVERY SCRAPE FUNCTION LOOKS THE WAY IT DOES
--------------------------------------------------
Scraping is even less reliable than calling a real API (see api_client.py
for that comparison): there's no guaranteed response shape at all, no
versioned contract, and the site's HTML structure can change without any
notice. Every function here assumes that can happen and fails safely
(empty list) rather than crashing the whole patient system over a page
layout change on a practice website.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Real websites often block or rate-limit requests that don't look like
# they came from a real browser (no User-Agent header at all is a common
# giveaway of a bot/script). Sending a realistic User-Agent is basic
# scraping etiquette -- it identifies us as SOME kind of browser, rather
# than pretending to be a specific real user, which would be misleading.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

QUOTES_BASE_URL = "https://quotes.toscrape.com"
BOOKS_BASE_URL = "https://books.toscrape.com"

# The tags we're filtering quotes for. Lowercased here so every comparison
# later can also lowercase the scraped tag text and compare like-for-like,
# without worrying about "Science" vs "science" capitalization mismatches.
HEALTH_RELATED_TAGS = ("science", "medicine", "health", "inspirational")

# Same idea, but for matching against BOOK TITLES instead of quote tags.
HEALTH_RELATED_TITLE_WORDS = ("health", "medicine", "nursing")

REQUEST_TIMEOUT_SECONDS = 10

# Where the scraped results get saved so the menu option can load them
# instantly next time instead of re-scraping on every single use.
DATA_DIR = Path(__file__).resolve().parent / "data"
QUOTES_OUTPUT_FILE = DATA_DIR / "scraped_quotes.json"


# ---------------------------------------------------------------------------
# QUOTES SCRAPER (required)
# ---------------------------------------------------------------------------

def scrape_health_quotes(max_pages=10):
    """Scrape quotes.toscrape.com and return quotes tagged with anything
    in HEALTH_RELATED_TAGS ("science", "medicine", "health").

    Args:
        max_pages (int): safety ceiling on how many pages to walk before
            giving up, even if the site claims there's a "next" page.
            Prevents an infinite loop if the site's pagination ever
            behaves unexpectedly (e.g. a "next" link that loops back to
            itself).

    Returns:
        list[dict]: each dict shaped as
            {"text": str, "author": str, "tags": list[str]}
            Returns an EMPTY LIST (never raises) on any network failure,
            or if no quotes matched the target tags.
    """
    matching_quotes = []
    # quotes.toscrape.com paginates as /page/1/, /page/2/, etc. We start
    # at page 1 and keep going until either we hit max_pages, or the page
    # itself tells us there's no "next" page left.
    page_number = 2
    while page_number <= max_pages:
        url = f"{QUOTES_BASE_URL}/page/{page_number}/"

        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            print(f"⚠ Quote scrape failed: no network connection ({url}).")
            break
        except requests.exceptions.Timeout:
            print(f"⚠ Quote scrape failed: request to {url} timed out.")
            break
        except requests.exceptions.HTTPError as e:
            # A 404 here most likely means we've walked past the last
            # real page (shouldn't normally happen since we check for a
            # "next" link below, but this is a safety net either way).
            print(f"⚠ Quote scrape failed: HTTP error on {url} ({e}).")
            break
        except requests.exceptions.RequestException as e:
            print(f"⚠ Quote scrape failed: unexpected request error ({e}).")
            break

        # BeautifulSoup parses the raw HTML text into a navigable tree we
        # can search. "lxml" is the underlying parser engine -- it's
        # faster and stricter than Python's built-in "html.parser".
        soup = BeautifulSoup(response.text, "lxml")

        # --- soup.find_all(): grab every quote block on this page -----
        # Each quote on the page is wrapped in <div class="quote">...
        # find_all() returns EVERY tag matching this description, as a
        # list, in the order they appear on the page.
        quote_divs = soup.find_all("div", class_="quote")

        if not quote_divs:
            # No quote blocks found at all -- either the site's HTML
            # structure changed, or we've somehow gone past real content.
            # Either way, stop rather than looping on empty pages.
            break

        for quote_div in quote_divs:
            # .find() (singular) grabs the FIRST match inside this one
            # quote_div, not the whole page -- we're now searching
            # WITHIN a single quote block, not the whole soup.
            text_span = quote_div.find("span", class_="text")
            author_tag = quote_div.find("small", class_="author")

            quote_text = text_span.get_text(strip=True) if text_span else ""
            author_name = author_tag.get_text(strip=True) if author_tag else "Unknown"

            # --- soup.select(): CSS-selector based extraction --------
            # ".tags a.tag" means: inside this quote_div, find every <a>
            # tag with class "tag" that lives inside an element with
            # class "tags". CSS selectors are often more compact than
            # chained find() calls once you're targeting nested elements
            # by class, which is exactly the case here.
            tag_elements = quote_div.select(".tags a.tag")
            quote_tags = [tag.get_text(strip=True) for tag in tag_elements]

            # Case-insensitive check: does ANY of this quote's tags
            # contain (or exactly match) one of our target keywords?
            # We lowercase both sides so "Science" and "science" are
            # treated as the same thing.
            tags_lowercased = [t.lower() for t in quote_tags]
            is_health_related = any(
                keyword in tag for tag in tags_lowercased
                for keyword in HEALTH_RELATED_TAGS
            )

            if is_health_related:
                matching_quotes.append({
                    "text": quote_text,
                    "author": author_name,
                    "tags": quote_tags,
                })

        # --- Pagination: is there a next page? -------------------------
        # soup.select_one() returns the FIRST element matching a CSS
        # selector, or None if nothing matches. "li.next a" means: an
        # <a> tag inside an <li class="next">. If this element doesn't
        # exist, we've reached the last page and should stop.
        next_link = soup.select_one("li.next a")
        if next_link is None:
            break

        page_number += 1

        # Be a polite scraper: pause between requests so we're not
        # hammering the server with back-to-back page loads. Only sleep
        # if we're actually about to make another request (no point
        # sleeping after the very last page).
        if page_number <= max_pages:
            time.sleep(1)

    return matching_quotes


def save_quotes_to_json(quotes, filepath=QUOTES_OUTPUT_FILE):
    """Save scraped quotes to a JSON file, tagged with the time they were
    scraped, so a caller loading the file later knows how fresh it is.

    Args:
        quotes (list[dict]): the quotes to save (as returned by
            scrape_health_quotes()).
        filepath (Path): where to write the JSON file. Defaults to
            data/scraped_quotes.json next to this module.

    Returns:
        bool: True if the save succeeded, False otherwise. Mirrors the
        style of save_registry() in file_manager.py -- a boolean result
        the caller can check, rather than an exception the caller must
        remember to catch.
    """
    # Make sure the data/ directory exists before trying to write into
    # it -- this is defensive: if someone deletes data/ by hand, we
    # recreate it instead of crashing on a missing-directory error.
    filepath.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        # ISO 8601 format (e.g. "2026-08-22T10:15:00") is the standard,
        # unambiguous way to store a timestamp in JSON -- it sorts
        # correctly as plain text and every language can parse it.
        "scraped_at": datetime.now().isoformat(),
        "quote_count": len(quotes),
        "quotes": quotes,
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            # indent=2 makes the saved JSON file human-readable if you
            # open it directly, at the (tiny, worthwhile) cost of a
            # slightly larger file than fully compact JSON.
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        print(f"⚠ Could not save quotes to {filepath}: {e}")
        return False


def load_quotes_from_json(filepath=QUOTES_OUTPUT_FILE):
    """Load previously-scraped quotes from disk, if the file exists.

    Returns:
        dict | None: the full saved payload (with "scraped_at",
        "quote_count", "quotes" keys), or None if the file doesn't exist
        yet or can't be read/parsed.
    """
    if not filepath.exists():
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"⚠ Could not read saved quotes at {filepath}: {e}")
        return None


# ---------------------------------------------------------------------------
# BOOKS SCRAPER (bonus)
# ---------------------------------------------------------------------------

def scrape_health_books(max_pages=5):
    """BONUS: scrape books.toscrape.com and return books whose TITLE
    contains "health", "medicine", or "nursing".

    Args:
        max_pages (int): safety ceiling on how many catalogue pages to
            walk, same reasoning as scrape_health_quotes().

    Returns:
        list[dict]: each dict shaped as {"title": str, "price": float}.
        Returns an EMPTY LIST (never raises) on failure or no matches.
    """
    matching_books = []
    page_number = 1

    while page_number <= max_pages:
        # books.toscrape.com's homepage IS page 1; every page after that
        # follows the pattern catalogue/page-2.html, catalogue/page-3.html
        url = (
            f"{BOOKS_BASE_URL}/index.html" if page_number == 1
            else f"{BOOKS_BASE_URL}/catalogue/page-{page_number}.html"
        )

        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            print(f"⚠ Book scrape failed: no network connection ({url}).")
            break
        except requests.exceptions.Timeout:
            print(f"⚠ Book scrape failed: request to {url} timed out.")
            break
        except requests.exceptions.HTTPError as e:
            # A 404 here means we've walked past the last real page --
            # normal end-of-catalogue condition, not an error worth
            # alarming the user about.
            if response.status_code == 404:
                break
            print(f"⚠ Book scrape failed: HTTP error on {url} ({e}).")
            break
        except requests.exceptions.RequestException as e:
            print(f"⚠ Book scrape failed: unexpected request error ({e}).")
            break

        soup = BeautifulSoup(response.text, "lxml")

        # CSS-selector extraction: every book on the page is an
        # <article class="product_pod">.
        book_articles = soup.select("article.product_pod")
        if not book_articles:
            break

        for article in book_articles:
            # The book's FULL title is stored in the <a> tag's "title"
            # attribute, not its visible text (the visible text gets
            # truncated with "..." on this site for long titles, so the
            # attribute is the only reliable source of the complete title).
            title_link = article.find("h3").find("a")
            full_title = title_link.get("title", "").strip()

            price_tag = article.select_one("p.price_color")
            price_text = price_tag.get_text(strip=True) if price_tag else ""
            # Prices are shown as "£54.23" -- strip the currency symbol
            # and convert to float so callers get a real number, not a
            # string they'd have to parse themselves.
            price_value = _parse_price(price_text)

            if any(word in full_title.lower() for word in HEALTH_RELATED_TITLE_WORDS):
                matching_books.append({
                    "title": full_title,
                    "price": price_value,
                })

        next_link = soup.select_one("li.next a")
        if next_link is None:
            break

        page_number += 1
        if page_number <= max_pages:
            time.sleep(1)

    return matching_books


def _parse_price(price_text):
    """Convert a price string like '£54.23' into a float (54.23).

    Kept as a small private helper (leading underscore) since price
    parsing is an internal formatting detail, reused by both the books
    scraper here and by price_tracker.py's own copy of this same logic.

    Returns 0.0 (never raises) if the text can't be parsed as a price --
    a missing/garbled price shouldn't crash an entire scrape over one
    book.
    """
    # Keep only digits and the decimal point, discarding the currency
    # symbol and any stray whitespace/formatting characters.
    cleaned = "".join(ch for ch in price_text if ch.isdigit() or ch == ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# STANDALONE DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== news_scraper.py self-test demo ===\n")

    print("-- scrape_health_quotes() --")
    quotes = scrape_health_quotes(max_pages=10)
    if quotes:
        for q in quotes:
            print(f"  \"{q['text']}\" — {q['author']} {q['tags']}")
    else:
        print("  No health/science/medicine-tagged quotes found "
              "(or the scrape failed -- see any warning above). "
              "This is a small fixed practice dataset, so an empty "
              "result here can be genuinely correct, not a bug.")

    print("\n-- save_quotes_to_json() / load_quotes_from_json() --")
    if save_quotes_to_json(quotes):
        print(f"  Saved {len(quotes)} quote(s) to {QUOTES_OUTPUT_FILE}")
        reloaded = load_quotes_from_json()
        if reloaded:
            print(f"  Reloaded file scraped_at={reloaded['scraped_at']}, "
                  f"quote_count={reloaded['quote_count']}")

    print("\n-- scrape_health_books() (BONUS) --")
    books = scrape_health_books(max_pages=5)
    if books:
        for b in books:
            print(f"  {b['title']} — £{b['price']:.2f}")
    else:
        print("  No health/medicine/nursing-titled books found "
              "(or the scrape failed -- see any warning above).")
