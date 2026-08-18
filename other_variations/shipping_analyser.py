"""
shipping_analyser.py

Logistics variation of Lesson 20's API-client exercise (Task 20B).

This is a STANDALONE script -- no imports from src/ or the patient
system. It reuses the same networking PRINCIPLES as api_client.py
(timeouts, try/except around every call, params= dicts, graceful
failure) applied to a completely different domain: shipping routes
between country pairs for a logistics company.
"""

import time

import requests

REQUEST_TIMEOUT_SECONDS = 10

# The country PAIRS we want routing information for. Each tuple is
# (origin, destination), using names the REST Countries API can match.
ROUTES = [
    ("Nigeria", "United Kingdom"),
    ("Nigeria", "United States"),
    ("Nigeria", "China"),
    ("Nigeria", "South Africa"),
]


def get_country_details(country_name):
    """Fetch region, timezone, and currency details for one country.

    API used: https://restcountries.com/v3.1/name/{country_name}
    (REST Countries API -- public, no key required)

    Demonstrates using the `params=` dict (rather than hand-building the
    URL) to ask the API for only the specific FIELDS we need, via REST
    Countries' `fields` filter option. This is both good practice
    (smaller response, faster parse) and satisfies the task requirement
    to use `params=` on at least one request.

    Args:
        country_name (str): country's common name, e.g. "Nigeria".

    Returns:
        dict | None: {
            "name": str,
            "region": str,
            "timezones": list[str],
            "currencies": str,   # human-readable, e.g. "NGN (Nigerian naira)"
        }
        Returns None on any failure (network, not found, bad response) --
        this function never raises out to its caller.
    """
    url = f"https://restcountries.com/v3.1/name/{country_name}"

    # `params=` builds the query string safely for us. Here we ask REST
    # Countries to return ONLY the fields we actually use, instead of its
    # full (much larger) default payload.
    params = {"fields": "name,region,timezones,currencies"}

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"⚠ No network connection -- could not look up '{country_name}'.")
        return None
    except requests.exceptions.Timeout:
        print(f"⚠ Request for '{country_name}' timed out after "
              f"{REQUEST_TIMEOUT_SECONDS} seconds.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"⚠ HTTP error looking up '{country_name}': {e}")
        return None
    except requests.exceptions.RequestException as e:
        # Catch-all fallback for anything not covered above (e.g. a
        # malformed URL, an SSL problem) -- keeps the whole script alive
        # even if something unexpected goes wrong with this one request.
        print(f"⚠ Unexpected network error looking up '{country_name}': {e}")
        return None

    try:
        payload = response.json()
        print(type(payload))
    except ValueError:
        print(f"⚠ Unreadable response looking up '{country_name}'.")
        return None

    if not payload:
        print(f"ℹ No match found for '{country_name}'.")
        return None

    if isinstance(payload, list):
        country = payload[0]
    else:
        country = payload

    # Currencies come back as a dict keyed by currency code, e.g.
    #   {"NGN": {"name": "Nigerian naira", "symbol": "₦"}}
    # We flatten that into one readable string per currency.
    currencies_raw = country.get("currencies", {})
    currency_strings = [
        f"{code} ({details.get('name', 'Unknown')})"
        for code, details in currencies_raw.items()
    ]

    return {
        "name": country.get("name", {}).get("common", country_name),
        "region": country.get("region", "Unknown"),
        "timezones": country.get("timezones", []),
        "currencies": ", ".join(currency_strings) if currency_strings else "Unknown",
    }


def print_route(origin_name, destination_name, origin_info, destination_info):
    """Print one formatted route block. Handles either side being None
    (a failed lookup) without crashing -- a partial result is still
    useful to a logistics planner, and is far better than the whole
    report dying because ONE of eight lookups failed.
    """
    print("\n" + "=" * 60)
    print(f"ROUTE: {origin_name} → {destination_name}")
    print("=" * 60)

    for label, info in (("ORIGIN", origin_info), ("DESTINATION", destination_info)):
        print(f"\n  {label}")
        if info is None:
            print("    (data unavailable -- lookup failed, see warning above)")
            continue
        print(f"    Country    : {info['name']}")
        print(f"    Region     : {info['region']}")
        print(f"    Timezones  : {', '.join(info['timezones']) if info['timezones'] else 'Unknown'}")
        print(f"    Currencies : {info['currencies']}")


if __name__ == "__main__":
    print("=== Shipping Zone Analyser ===")
    print(f"Analysing {len(ROUTES)} route(s)...\n")

    for origin, destination in ROUTES:
        origin_info = get_country_details(origin)
        # A short, kind pause between calls -- staying comfortably under
        # any free-tier rate limit, exactly as the lesson's rate-limit
        # warning asks for when calling an API in a loop.
        time.sleep(0.5)
        destination_info = get_country_details(destination)
        time.sleep(0.5)

        print_route(origin, destination, origin_info, destination_info)

    print("\n" + "=" * 60)
    print("Done.")
