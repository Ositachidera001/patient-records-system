"""
api_client.py

Dedicated module for every external (internet-facing) API call the patient
system makes. Nothing else in this codebase should import `requests`
directly -- if a new feature needs to call an external service, the
function belongs HERE, not scattered into patient_ops.py.

WHY THIS SEPARATION MATTERS
----------------------------
1. External APIs are the LEAST reliable part of any system: the network
   can drop, the API can be slow, the API can be down, the API can change
   its response shape without warning. Every single function in this file
   is written to assume ALL of that will eventually happen, and to fail
   *safely* (return None / an empty list) rather than crash the whole
   patient system over a lookup that was only ever "nice to have".
2. Keeping all network code in one file means there's exactly ONE place
   that needs a timeout, ONE place that needs exception handling, and ONE
   place to update if an API's URL or response format ever changes.
3. A patient system's CORE job (registering, tracking, discharging
   patients) must keep working even with zero internet access. These
   lookups are a convenience layered on top -- never a dependency.

APIS USED IN THIS FILE
------------------------
- OpenFDA Drug Label API : https://api.fda.gov/drug/label.json
  Public, no API key required for light use (~240 requests/minute).
- REST Countries API     : "https://api.restcountries.com/countries/v5?q={country_name}
    (REST Countries API -- no more public, new version now requires API key)
"""
import requests
import time

def get_country_info(country_name: str) -> dict | None:
    """fetch basic health-relevant country information from the REST Countries API.
    
    Uses https://restcountries.com - free, no API key required.
    Returns a dict with name, population, capital, region, and languages.
    Returns None on any error.
    """
    rest_country_api_key="rc_live_750f428588ba4ca1823e2632f0aae0d5"
    headers = {'Authorization': f'Bearer {rest_country_api_key}'}
    url = f"https://api.restcountries.com/countries/v5?q={country}"


    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        country = data[0]

        return {"name": country.get["name"]["common"],
                "capital":country.get("capital", ["unknown"])[0],
                "region": country["region"],
                "population": country["population"],
                "languages": list(country.get("languages", {}).values()),
                }

    except requests.exceptions.ConnectionError:
        print("no internet")
        return None
    except requests.exceptions.Timeout:
        print("timeout")
        return None
    except requests.exceptions.HTTPError as e:
        print("http error", e.response.status_code)
        return None
    except (KeyError, IndexError) as e:
        print("unexpected api structure")
        return None

def lookup_drug(drug_name: str, limit: int = 3) -> list:
    """search OpenFDA for drug label information. 
    OpenFDA is the US FDA's open data API - free no API key required for limited queries.
    Useful for adverse reactions and drug descriptions that a Health IT system might display as reference information
    
    API docs: https://open.fda.gov/apis/drug/label/
    """
    url = "https://api.fda.gov.drug/label.json"
    params = {"search": f"openfda.generic_name:{drug_name}",
              "limit": limit
        }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(response.status_code if not response.raise_for_status else response.raise_for_status)
        data = response.json()

        results = []
        for item in data.get("results", []):
            results.append({"brand_name": item.get("openfda", {}).get("brand_name", ["unknown"])[0],
                            "generic_name": item.get("openfda", {}).get("generic_name", ["unknwon"])[0],
                            "purpose": item.get("purpose", ["not available"])[0][:200],
                            })
        return results
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"⚠ No result found for '{drug_name}'")
        elif e.response.status_code == 429:
            print(f"⚠ wait limit hit - wait before retrying")
        else:
            print(f"❌ API error: {e.response.status_code}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Networ error: {e}")
        return []
        import requests

import time

REQUEST_TIMEOUT_SECONDS = 10
def _first_or_default(value_list, default):
    """Small shared helper: OpenFDA fields are usually LISTS of strings
    (e.g. ["IBUPROFEN"]) even when there's only one value. This safely
    grabs the first entry, or falls back to `default` if the field is
    missing, None, or an empty list.

    Kept private (leading underscore) because it's an internal formatting
    detail of this module, not something other files should call.
    """
    if value_list and isinstance(value_list, list):
        return value_list[0]
    return default


def lookup_drug(drug_name, limit=3):
    """Look up a drug by name in the OpenFDA drug label database.

    API used: https://api.fda.gov/drug/label.json
    (OpenFDA Drug Label API -- public, no key required for light use)

    Args:
        drug_name (str): the drug's brand or generic name to search for,
            e.g. "ibuprofen" or "paracetamol".
        limit (int): maximum number of label records to return. OpenFDA
            caps this itself, but we pass it explicitly so callers can
            request fewer results (default 3) instead of always pulling
            the maximum.

    Returns:
        list[dict]: a list of simplified drug-info dicts, each shaped as
            {
                "brand_name": str,
                "generic_name": str,
                "purpose": str,
                "warnings": str,
            }
            Returns an EMPTY LIST (never None, never raises) if the drug
            isn't found, the network fails, or anything else goes wrong.
            An empty list is safe for a caller to loop over with `for`
            without needing a separate "is this None?" check first.
    """
    url = "https://api.fda.gov/drug/label.json"

    # OpenFDA's search syntax: `search=field:"value"` inside the query
    # string. Using the `params=` dict (instead of hand-building the URL
    # with string concatenation/f-strings) lets the `requests` library
    # handle URL-encoding for us -- spaces, quotes, and special characters
    # in `drug_name` are escaped correctly automatically, which is easy to
    # get wrong by hand.
    params = {
        "search": f'openfda.brand_name:"{drug_name}" '
                  f'openfda.generic_name:"{drug_name}"',
        "limit": limit,
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        # raise_for_status() turns an HTTP error status (404, 500, etc.)
        # into a Python exception (HTTPError) instead of silently letting
        # us try to parse an error page as if it were drug data.
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        # No internet, DNS failure, server unreachable, etc.
        print("⚠ Drug lookup failed: no network connection to OpenFDA.")
        return []
    except requests.exceptions.Timeout:
        # The server didn't respond within REQUEST_TIMEOUT_SECONDS.
        print(f"⚠ Drug lookup failed: OpenFDA did not respond within "
              f"{REQUEST_TIMEOUT_SECONDS} seconds.")
        return []
    except requests.exceptions.HTTPError as e:
        # OpenFDA returns 404 when nothing matches the search -- that's a
        # normal "no results" case for this API, not a system failure,
        # so we report it quietly rather than as an alarming error.
        if response.status_code == 404:
            print(f"ℹ No drug information found for '{drug_name}'.")
        else:
            print(f"⚠ Drug lookup failed: HTTP error ({e}).")
        return []
    except requests.exceptions.RequestException as e:
        # Final fallback: catches ANY other requests-library exception we
        # didn't specifically anticipate above. requests.exceptions.
        # RequestException is the common base class every other requests
        # exception inherits from, so this is our safety net -- it must
        # be the LAST except block, or it would swallow the more specific
        # exceptions above before they ever get a chance to run.
        print(f"⚠ Drug lookup failed: unexpected request error ({e}).")
        return []

    try:
        payload = response.json()
        results = payload.get("results", [])
    except (ValueError, AttributeError):
        # response.json() raises ValueError if the body isn't valid JSON
        # at all (e.g. OpenFDA served an HTML error page instead).
        print("⚠ Drug lookup failed: OpenFDA returned an unreadable response.")
        return []

    # Reshape OpenFDA's verbose, deeply-nested records into a small, flat
    # dict that's easy for the menu display code to print. Every field is
    # fetched defensively with .get(...) and a fallback, because OpenFDA
    # label records are user-submitted and inconsistently populated --
    # not every drug label has every field.
    simplified = []
    for record in results:
        openfda = record.get("openfda", {})
        simplified.append({
            "brand_name": _first_or_default(openfda.get("brand_name"), "Unknown"),
            "generic_name": _first_or_default(openfda.get("generic_name"), "Unknown"),
            "purpose": _first_or_default(record.get("purpose"), "Not listed"),
            "warnings": _first_or_default(record.get("warnings"), "Not listed"),
        })

    return simplified

def check_drug_interaction_warning(drug1, drug2):
    """BONUS: check whether two drugs' OpenFDA warning text mentions the
    other drug by name -- a basic, genuinely useful clinical safety net.

    API used: https://api.fda.gov/drug/label.json
    (OpenFDA Drug Label API -- same endpoint as lookup_drug(), queried
    once per drug)

    IMPORTANT SAFETY NOTE: this is a teaching exercise, NOT a substitute
    for a real clinical drug-interaction database or a pharmacist's
    judgement. It only checks whether one drug's warning TEXT happens to
    mention the other drug's name -- it cannot detect interactions that
    are real but simply not worded that way in the label text.

    Args:
        drug1 (str): first drug name.
        drug2 (str): second drug name.

    Returns:
        dict: {
            "checked": bool,       # True if both lookups succeeded
            "interaction_found": bool,
            "message": str,        # human-readable summary for display
        }
        If either lookup fails (network issue, drug not found), returns
        {"checked": False, "interaction_found": False, "message": "..."}
        rather than raising -- callers can always safely read every key.
    """
    # time.sleep() between the two calls is a "be kind to the free API"
    # courtesy pause, per the lesson's rate-limit warning -- OpenFDA
    # allows ~240 requests/minute, and two calls back-to-back are well
    # within that, but the pause costs us nothing and protects against
    # this function ever being called in a tight loop later.
    results1 = lookup_drug(drug1, limit=1)
    time.sleep(0.5)
    results2 = lookup_drug(drug2, limit=1)

    if not results1:
        return {
            "checked": False,
            "interaction_found": False,
            "message": f"⚠ Could not check interactions: no OpenFDA "
                       f"record found for '{drug1}'.",
        }
    if not results2:
        return {
            "checked": False,
            "interaction_found": False,
            "message": f"⚠ Could not check interactions: no OpenFDA "
                       f"record found for '{drug2}'.",
        }

    warnings1 = results1[0]["warnings"].lower()
    warnings2 = results2[0]["warnings"].lower()

    # A simple, honest substring check: does drug2's name appear in
    # drug1's warning text, or vice versa? Real interaction checking
    # needs a proper drug-interaction database -- this is a lightweight
    # heuristic on top of label text, and we say so plainly in the
    # message either way.
    mentions_in_1 = drug2.lower() in warnings1
    mentions_in_2 = drug1.lower() in warnings2

    if mentions_in_1 or mentions_in_2:
        return {
            "checked": True,
            "interaction_found": True,
            "message": (
                f"🔴 POTENTIAL INTERACTION: '{drug1}' and '{drug2}' each "
                f"appear in the other's OpenFDA warning text. Confirm "
                f"with a pharmacist before co-administering."
            ),
        }

    return {
        "checked": True,
        "interaction_found": False,
        "message": (
            f"🟢 No direct mention of '{drug2}' in '{drug1}''s warnings "
            f"(or vice versa) on OpenFDA. This does NOT guarantee "
            f"safety -- always confirm with a pharmacist."
        ),
    }

def get_country_health_info(country_name):
    """Look up population and region data for a country, for patient
    nationality/context purposes.

    API used: "https://api.restcountries.com/countries/v5?q={country_name}
    (REST Countries API -- no more public, new version now requires API key)

    Args:
        country_name (str): the country's common name, e.g. "Nigeria".

    Returns:
        dict | None: {
            "name": str,
            "region": str,
            "subregion": str,
            "population": int,
            "capital": str,
        }
        Returns None (never raises) if the country isn't found or the
        request fails for any reason.
    """
    rest_country_api_key="rc_live_750f428588ba4ca1823e2632f0aae0d5"
    headers = {'Authorization': f'Bearer {rest_country_api_key}'}
    url = f"https://api.restcountries.com/countries/v5?q={country_name}"

    # This endpoint takes the country name as part of the URL PATH, not
    # as a query parameter, so there's no `params=` dict to build here --
    # see shipping_analyser.py's routing lookup for an example of this
    # same API used WITH `params=` (its "fields" filter option).
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("⚠ Country lookup failed: no network connection to REST Countries.")
        return None
    except requests.exceptions.Timeout:
        print(f"⚠ Country lookup failed: no response within "
              f"10 seconds.")
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"ℹ No country found matching '{country_name}'.")
        else:
            print(f"⚠ Country lookup failed: HTTP error ({e}).")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠ Country lookup failed: unexpected request error ({e}).")
        return None

    try:
        data = response.json()
    except ValueError:
        print("⚠ Country lookup failed: unreadable response from REST Countries.")
        return None

    if not data:
        return None

    # REST Countries returns a LIST of matches (a name search can be
    # ambiguous, e.g. "Georgia" the country vs partial matches) -- we
    # take the first, best match for a simple single-result lookup.
    country = data['data']['objects'][0]
    # print(type(country))
    return {
        "name": country.get("names", {}).get("common", country_name),
        "region": country.get("region", "Unknown"),
        "subregion": country.get("subregion", "Unknown"),
        "population": country.get("population", 0),
        "capital": _first_or_default(country.get("capitals"), {}).get("name", "Unknown"),
    }

# ---------------------------------------------------------------------------
# STANDALONE DEMO
# Runs only when this file is executed directly. Because these functions
# depend on live internet access, this demo will print clear network-
# failure messages (rather than crashing) if run somewhere offline --
# which is itself a demonstration that the error handling works.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== api_client.py self-test demo ===\n")

    print("-- lookup_drug('ibuprofen') --")
    drug_results = lookup_drug("ibuprofen", limit=2)
    if drug_results:
        for drug in drug_results:
            print(f"  Brand: {drug['brand_name']} | Generic: {drug['generic_name']}")
            print(f"  Purpose: {drug['purpose'][:80]}...")
    else:
        print("  (no results / lookup failed -- see message above)")

    time.sleep(0.5)  # be kind to the free API between demo calls

    print("\n-- get_country_health_info('Nigeria') --")
    country_info = get_country_health_info("Nigeria")
    if country_info:
        print(f"  {country_info['name']}: {country_info['region']} / "
              f"{country_info['subregion']}, population "
              f"{country_info['population']:,}, capital "
              f"{country_info['capital']}")
    else:
        print("  (no result / lookup failed -- see message above)")

    time.sleep(0.5)

    print("\n-- check_drug_interaction_warning('warfarin', 'aspirin') (BONUS) --")
    interaction = check_drug_interaction_warning("warfarin", "aspirin")
    print(f"  {interaction['message']}")


if __file__ == "__main__":
    # drugs = lookup_drug("paracetamol", limit= 3)
    # for drug in drugs:
    #     print(f"\nBrand           : {drug['brand_name']}")
    #     print(f"Generic           : {drug['generic_name']}")
    #     print(f"Ourpose            : {drug['purpose'][:100]}...")

    info = get_country_info("Nigeria")

    if info:
        print(f"Country           : {info['name']}")
        print(f"Capital           : {info['capital']}")
        print(f"Region            : {info['region']}")
        print(f"Population        : {info['population']}")
        print(f"Languages         : {info['languages']}")