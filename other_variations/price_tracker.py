"""
price_tracker.py

E-commerce variation of Lesson 21's scraping exercise (Task 21B).

Standalone script -- no imports from src/. Scrapes the books.toscrape.com
homepage (a practice/demo bookstore site, not a real store) and builds a
simple price-monitoring snapshot: every book's title, price, and star
rating, saved to a timestamped JSON file, with summary stats printed to
the terminal.
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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

BOOKS_URL = "https://books.toscrape.com/index.html"
REQUEST_TIMEOUT_SECONDS = 10

# books.toscrape.com encodes the star rating as a CSS CLASS NAME written
# out in English words (e.g. class="star-rating Three"), not as a number
# or a data attribute. This lookup table converts that word back into a
# usable integer so we can do actual math on it (averages, sorting, etc).
RATING_WORDS_TO_NUMBERS = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

# Saved next to this script, timestamped so each run keeps its own
# snapshot rather than overwriting the previous one.
OUTPUT_DIR = Path(__file__).resolve().parent
SNAPSHOT_FILENAME_FORMAT = "price_snapshot_%Y%m%d_%H%M%S.json"


def _parse_price(price_text):
    """Convert a price string like '£54.23' into a float (54.23).

    Returns 0.0 (never raises) if the text can't be parsed -- a single
    unreadable price shouldn't crash the whole scrape.
    """
    cleaned = "".join(ch for ch in price_text if ch.isdigit() or ch == ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_rating(star_rating_tag):
    """Read the star rating off a book's <p class="star-rating X"> tag.

    The rating word (One/Two/.../Five) is just ONE of possibly several
    CSS classes on this tag (the other being the literal "star-rating"
    class itself), so we can't just read "the class" -- we have to look
    through ALL of the tag's classes and find the one that's a rating
    word we recognise.

    Returns 0 (never raises) if no recognisable rating word is found --
    e.g. if the site's markup ever changes this class-naming scheme.
    """
    if star_rating_tag is None:
        return 0

    # .get("class") on a BeautifulSoup tag returns a LIST of every class
    # name on that element, e.g. ["star-rating", "Three"] -- HTML allows
    # multiple classes on one element, space-separated, and BeautifulSoup
    # gives them back to us already split into a list.
    css_classes = star_rating_tag.get("class", [])
    for css_class in css_classes:
        if css_class in RATING_WORDS_TO_NUMBERS:
            return RATING_WORDS_TO_NUMBERS[css_class]
    return 0


def scrape_book_prices():
    """Scrape every book on the books.toscrape.com homepage.

    Returns:
        list[dict]: each shaped as
            {"title": str, "price": float, "rating": int}
        Returns an EMPTY LIST (never raises) on any failure.
    """
    try:
        response = requests.get(BOOKS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"⚠ Could not reach {BOOKS_URL} — no network connection.")
        return []
    except requests.exceptions.Timeout:
        print(f"⚠ Request to {BOOKS_URL} timed out after "
              f"{REQUEST_TIMEOUT_SECONDS} seconds.")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"⚠ HTTP error fetching {BOOKS_URL}: {e}")
        return []
    except requests.exceptions.RequestException as e:
        # Catch-all for anything not covered above -- keeps the script
        # from crashing over an unanticipated networking problem.
        print(f"⚠ Unexpected network error fetching {BOOKS_URL}: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")

    # CSS-selector extraction (satisfies the "use soup.select() for at
    # least one extraction" requirement): every book on the page is an
    # <article class="product_pod">.
    book_articles = soup.select("article.product_pod")

    books = []
    for article in book_articles:
        title_link = article.find("h3").find("a")
        full_title = title_link.get("title", "").strip()

        price_tag = article.select_one("p.price_color")
        price_text = price_tag.get_text(strip=True) if price_tag else ""

        rating_tag = article.select_one("p.star-rating")
        rating = _parse_rating(rating_tag)

        books.append({
            "title": full_title,
            "price": _parse_price(price_text),
            "rating": rating,
        })

    return books


def save_snapshot(books):
    """Save a timestamped JSON snapshot of the scraped books.

    Returns:
        Path | None: the path the snapshot was written to, or None if
        saving failed.
    """
    timestamp = datetime.now()
    filename = timestamp.strftime(SNAPSHOT_FILENAME_FORMAT)
    filepath = OUTPUT_DIR / filename

    payload = {
        "scraped_at": timestamp.isoformat(),
        "book_count": len(books),
        "books": books,
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return filepath
    except OSError as e:
        print(f"⚠ Could not save snapshot to {filepath}: {e}")
        return None


def print_summary(books):
    """Print the required summary stats: total books, price range,
    average price, and the highest-rated book(s).
    """
    if not books:
        print("No books to summarise (scrape returned nothing).")
        return

    prices = [b["price"] for b in books]
    total_books = len(books)
    min_price = min(prices)
    max_price = max(prices)
    average_price = sum(prices) / total_books

    # Find the highest star rating present, then collect EVERY book that
    # shares that top rating -- there's often more than one 5-star book,
    # and picking just one would silently hide the others.
    highest_rating = max(b["rating"] for b in books)
    top_rated_books = [b for b in books if b["rating"] == highest_rating]

    print("\n" + "=" * 60)
    print("PRICE SNAPSHOT SUMMARY")
    print("=" * 60)
    print(f"Total books scraped : {total_books}")
    print(f"Price range          : £{min_price:.2f} – £{max_price:.2f}")
    print(f"Average price         : £{average_price:.2f}")
    print(f"Highest rating found  : {highest_rating} star(s)")
    print(f"Top-rated book(s) ({len(top_rated_books)}):")
    for book in top_rated_books:
        print(f"  - {book['title']} (£{book['price']:.2f})")
    print("=" * 60)


if __name__ == "__main__":
    print("=== Product Price Snapshot Tool ===")
    print(f"Scraping {BOOKS_URL} ...\n")

    books = scrape_book_prices()

    if books:
        snapshot_path = save_snapshot(books)
        if snapshot_path:
            print(f"Snapshot saved to: {snapshot_path}")
        print_summary(books)
    else:
        print("No books were scraped — see any warning above. "
              "Nothing to save or summarise.")
