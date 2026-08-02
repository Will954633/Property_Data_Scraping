#!/usr/bin/env python3
"""
curl_cffi Suburb Property Scraper — Chrome-free replacement for run_parallel_suburb_scrape.py
Created: 2026-03-13

Replaces Selenium/Chrome with curl_cffi (TLS-impersonating HTTP client).
Uses the same html_parser.py and MongoDB save logic as the original.

USAGE:
  python3 run_curlffi_suburb_scrape.py --suburbs "Robina:4226" "Varsity Lakes:4227"
  python3 run_curlffi_suburb_scrape.py --suburbs "Robina:4226" --max-concurrent 3 --parallel-properties 3
"""

import time
import os
import sys
import re
import json
import argparse
from datetime import datetime
from typing import Dict, Optional, List

# CRITICAL: Force unbuffered stdout so output is visible when launched via subprocess.Popen
# Without this, Python buffers stdout when it's a pipe (not a TTY), causing the orchestrator
# to think the process is hung.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)

from pymongo import MongoClient, ASCENDING
from pymongo.errors import OperationFailure
from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    print("ERROR: curl_cffi not installed!")
    print("Install with: pip3 install curl_cffi")
    sys.exit(1)

# Import the HTML parser from the existing production system
sys.path.append('../../07_Undetectable_method/00_Production_System/02_Individual_Property_Google_Search')
try:
    from html_parser import parse_listing_html, clean_property_data
except ImportError:
    print("ERROR: html_parser not found!")
    print("Make sure the path to html_parser.py is correct")
    sys.exit(1)

# Import scraping failures logger
sys.path.append('../../../Fields_Orchestrator/01_Debug_Log')
try:
    from scraping_failures_logger import log_scraping_failure
    FAILURES_LOGGING_ENABLED = True
except ImportError:
    print("WARNING: scraping_failures_logger not found - failure logging disabled")
    FAILURES_LOGGING_ENABLED = False
    def log_scraping_failure(*args, **kwargs):
        pass

# ── Configuration ──────────────────────────────────────────────────────────────

BETWEEN_PROPERTY_DELAY = 2      # seconds between property fetches
BETWEEN_PAGE_DELAY = 3          # seconds between discovery pages
MAX_PAGES = 20                  # max discovery pages per suburb
PAGE_REFETCH_MAX = 4           # max fetches of the SAME page to reach its full card count
                               # (Domain renders a variable subset of a page's listing
                               #  cards per request; we union URLs across fetches until we
                               #  match the page's authoritative ld+json Residence count)
MIN_LISTINGS_PER_PAGE = 5       # stop paginating when fewer than this
COSMOS_INTER_OP_DELAY = 0.3     # seconds before each MongoDB op (serverless throttle)
HTTP_TIMEOUT = 30               # seconds for curl_cffi requests
MAX_PROPERTY_RETRIES = 5        # retries per property detail fetch

MONITORED_FIELDS = ['price', 'inspection_times', 'agents_description']

TARGET_MARKET_SUBURBS = {
    'robina', 'mudgeeraba', 'varsity lakes', 'reedy creek',
    'burleigh waters', 'merrimac', 'worongary', 'carrara'
}

DATABASE_NAME = 'Gold_Coast'

# ── MongoDB connection ─────────────────────────────────────────────────────────

_mongo_client = None
_mongo_db = None


def get_mongodb_connection():
    """Get or create MongoDB connection (process-wide singleton)."""
    global _mongo_client, _mongo_db

    if _mongo_client is None:
        conn_str = (
            os.environ.get("COSMOS_CONNECTION_STRING")
            or os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017/")
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                _mongo_client = MongoClient(
                    conn_str,
                    maxPoolSize=50,
                    minPoolSize=10,
                    maxIdleTimeMS=45000,
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    retryWrites=False,
                    retryReads=False,
                )
                _mongo_db = _mongo_client[DATABASE_NAME]
                _mongo_client.admin.command('ping')
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"MongoDB connection attempt {attempt + 1} failed, retrying in 3s...")
                    time.sleep(3)
                else:
                    raise Exception(f"MongoDB connection failed after {max_retries} attempts: {e}")

    return _mongo_client, _mongo_db


# ── Canonical suburb whitelist ─────────────────────────────────────────────────
# Prevents malformed single-word suffixes (e.g. "Heads", "Lakes", "Valley")
# from creating non-canonical collections.  Keyed by lowercase suffix token.
SUFFIX_TO_CANONICAL = {
    'heads': 'Burleigh Heads',
    'lakes': 'Varsity Lakes',
    'vale': 'Willow Vale',
    'valley': 'Tallebudgera Valley',
    'well': 'Jacobs Well',
    'waters': 'Burleigh Waters',
    'beach': 'Mermaid Beach',
    'pines': 'Pacific Pines',
    'hills': 'Ormeau Hills',
    'island': 'Hope Island',
    'point': 'Paradise Point',
    'bay': 'Runaway Bay',
}

# Full list of known Gold Coast suburbs (lowercase) for validation
CANONICAL_SUBURBS = {
    'advancetown', 'alberton', 'arundel', 'ashmore', 'austinville',
    'beechmont', 'benowa', 'biggera waters', 'bilinga', 'bonogin',
    'broadbeach', 'broadbeach waters', 'bundall', 'burleigh heads',
    'burleigh waters', 'carrara', 'cedar creek', 'chevron island',
    'clear island waters', 'coolangatta', 'coombabah', 'coomera',
    'currumbin', 'currumbin valley', 'currumbin waters', 'elanora',
    'gaven', 'gilberton', 'gilston', 'guanaba', 'helensvale',
    'highland park', 'hollywell', 'hope island', 'jacobs well',
    'kingsholme', 'labrador', 'lower beechmont', 'luscombe',
    'main beach', 'maudsland', 'mermaid beach', 'mermaid waters',
    'merrimac', 'miami', 'molendinar', 'mount nathan', 'mudgeeraba',
    'natural bridge', 'nerang', 'neranwood', 'norwell',
    'numinbah valley', 'ormeau', 'ormeau hills', 'oxenford',
    'pacific pines', 'palm beach', 'paradise point', 'parkwood',
    'pimpama', 'reedy creek', 'robina', 'runaway bay',
    'south stradbroke', 'southern moreton bay islands', 'southport',
    'springbrook', 'stapylton', 'steiglitz', 'surfers paradise',
    'tallai', 'tallebudgera', 'tallebudgera valley', 'tugun',
    'upper coomera', 'varsity lakes', 'willow vale', 'wongawallan',
    'woongoolba', 'worongary', 'yatala',
}


def validate_suburb(suburb: str) -> Optional[str]:
    """Validate and correct a suburb name against the canonical whitelist.
    Returns the canonical suburb name (title-cased) or None if unrecognised.
    """
    if not suburb:
        return None
    lower = suburb.strip().lower()
    # Direct match against canonical set
    if lower in CANONICAL_SUBURBS:
        return suburb.strip().title()
    # Check if it's a known suffix truncation
    if lower in SUFFIX_TO_CANONICAL:
        return SUFFIX_TO_CANONICAL[lower]
    return None


# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_suburb_from_address(address: str) -> Optional[str]:
    """Extract suburb from address string.
    Example: '48 Peach Drive, Robina, QLD 4226' -> 'Robina'
    """
    if not address:
        return None
    match = re.search(r',\s*([^,]+),\s*(QLD|NSW|VIC|SA|WA|TAS|NT|ACT)', address, re.IGNORECASE)
    if match:
        raw = match.group(1).strip()
        # Validate against canonical list; if invalid, return None to trigger fallback
        validated = validate_suburb(raw)
        return validated if validated else raw
    return None


def _normalize_address_for_gis(street_address: str, suburb: str, postcode: str) -> str:
    """Build normalised GIS address: '12 GERSHWIN COURT NERANG QLD 4211' (uppercase, no commas)."""
    return f"{street_address} {suburb} QLD {postcode}".upper().strip()


def _mongo_op_with_retry(op, max_retries: int = 5):
    """Execute MongoDB op with Cosmos DB 429 retry and inter-op delay."""
    time.sleep(COSMOS_INTER_OP_DELAY)
    for attempt in range(max_retries):
        try:
            return op()
        except OperationFailure as e:
            if e.code == 16500:  # TooManyRequests
                match = re.search(r'RetryAfterMs=(\d+)', str(e))
                wait_ms = int(match.group(1)) if match else 1000
                time.sleep((wait_ms + 50) / 1000.0)
            else:
                raise
    raise OperationFailure(f"MongoDB op failed after {max_retries} retries (429)")


_BRIGHTDATA_ENDPOINT = 'https://api.brightdata.com/request'


def _fetch_via_brightdata(url: str) -> Optional[str]:
    """Fetch via Bright Data Web Unlocker (solves Akamai/Cloudflare challenges).
    Reads env at call time so callers can populate it after import."""
    api_key = os.environ.get('BRIGHTDATA_API_KEY')
    zone = os.environ.get('BRIGHTDATA_ZONE', 'web_unlocker2')
    if not api_key:
        return None
    try:
        resp = cffi_requests.post(
            _BRIGHTDATA_ENDPOINT,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
            json={'zone': zone, 'url': url, 'format': 'raw'},
            timeout=150,
        )
        if resp.status_code == 200 and len(resp.text) >= 500:
            return resp.text
        return None
    except Exception:
        return None


def _fetch(url: str, retries: int = 5) -> Optional[str]:
    """Fetch a URL via the hardened shared Bright Data helper, which handles retries,
    growing backoff, the x-brd-status-code header and Web Unlocker's min_size-502
    flakiness. The local _fetch_via_brightdata was markedly less reliable on Domain
    detail pages (≈1/3 success) — the shared helper gets ≈100% on the same URLs.
    Falls back to the local Web Unlocker / curl_cffi path if the shared module
    can't be imported."""
    try:
        import sys as _sys
        if '/home/fields/Fields_Orchestrator' not in _sys.path:
            _sys.path.insert(0, '/home/fields/Fields_Orchestrator')
        from shared.domain_fetch import fetch_html as _shared_fetch
        html = _shared_fetch(url, retries=retries, timeout=150)
        if html:
            return html
    except Exception:
        pass

    # Fallback: local Bright Data Web Unlocker, else direct curl_cffi
    use_unlocker = bool(os.environ.get('BRIGHTDATA_API_KEY'))
    for attempt in range(retries):
        if use_unlocker:
            html = _fetch_via_brightdata(url)
            if html:
                return html
        else:
            try:
                resp = cffi_requests.get(url, impersonate="chrome120", timeout=HTTP_TIMEOUT)
                if resp.status_code == 200:
                    return resp.text
                if resp.status_code == 404:
                    return None
            except Exception:
                pass
        if attempt < retries - 1:
            time.sleep(min(3 * (attempt + 1), 15))
    return None


def _addr_key(text: str):
    """Canonical (leading-number, street-name) key for matching a listed address
    against a listing-URL slug or a DB address. Collapses unit/building number
    runs to their leading token, so "40/170 Bardon Avenue", the slug
    "40-170-bardon-avenue" and the DB doc "40/170 Bardon Avenue, Burleigh Waters
    QLD 4220" all key identically. Used by both discovery (URL↔address resolution)
    and coverage recording (Domain-listed vs in-DB diff)."""
    t = (text or "").split(',')[0].lower().replace('-', ' ').replace('/', ' ')
    t = re.sub(r'\bunit\b|\bid:\d+\b', ' ', t)
    lead = re.match(r'\s*(\d+)', t)
    street = re.sub(r'^[\s\d]+', '', t).strip()
    return (lead.group(1) if lead else '', street)


# ── Scraper ────────────────────────────────────────────────────────────────────

class CurlCffiSuburbScraper:
    """Scrapes a single suburb using curl_cffi (no browser)."""

    # Fields that must never be overwritten by a re-scrape
    PIPELINE_FIELDS = {
        'first_seen',
        'watch_article_generated',
        'watch_article_path',
        'watch_article_generated_at',
    }

    # Image fields preserved when an active listing is re-scraped (blob URLs)
    IMAGE_FIELDS = {
        'property_images',
        'floor_plans',
        'property_images_original',
        'floor_plans_original',
        'images_uploaded_to_blob',
        'images_blob_uploaded_at',
        'image_history',
    }

    def __init__(self, suburb_name: str, postcode: str, full_rescrape: bool = False):
        self.suburb_name = suburb_name
        self.postcode = postcode
        # When False (default), existing for_sale listings are refreshed cheaply from
        # the search page (price + last_updated) instead of a full detail re-scrape;
        # only NEW listings are detail-scraped. Set True for a periodic deep refresh.
        self.full_rescrape = full_rescrape
        self.suburb_slug = suburb_name.lower().replace(' ', '-') + f"-qld-{postcode}"
        self.collection_name = suburb_name.lower().replace(' ', '_')

        # MongoDB
        self.log("Connecting to MongoDB...")
        self.mongo_client, self.db = get_mongodb_connection()
        self.collection = self.db[self.collection_name]
        self.log(f"MongoDB connected — Collection: {self.collection_name}")
        self._create_indexes()

        # Counters
        self.expected_count = None
        self.discovered_urls: List[str] = []
        # Every listed address seen in the search results' ld+json (the authoritative
        # per-page card list). Used to (a) gate discovery completeness per page and
        # (b) surface the specific addresses we could NOT resolve to a listing URL,
        # which feed the listing-coverage reconciliation / health board.
        self.discovered_addresses: set = set()
        self.unresolved_addresses: set = set()
        self.search_meta: Dict[str, Dict] = {}   # url -> {price} from search page __NEXT_DATA__
        self.successful = 0
        self.failed = 0
        self.refreshed = 0   # existing listings refreshed cheaply (no detail fetch)

    # ── Logging ────────────────────────────────────────────────────────────

    def log(self, message: str):
        print(f"[{self.suburb_name}] {message}")

    # ── Indexes ────────────────────────────────────────────────────────────

    def _create_indexes(self):
        try:
            # PARTIAL unique index: only enforce uniqueness on docs whose listing_url
            # is a string. A plain unique index fails to build (E11000) when multiple
            # docs have listing_url=null, leaving dedupe-by-URL unenforced.
            self.collection.create_index(
                [("listing_url", ASCENDING)], unique=True,
                partialFilterExpression={"listing_url": {"$type": "string"}},
            )
            self.collection.create_index([("address", ASCENDING)])
            self.collection.create_index([("last_updated", ASCENDING)])
            self.log("Indexes created/verified")
        except Exception as e:
            self.log(f"Index creation warning: {e}")

    # ── Phase 1: Discovery ─────────────────────────────────────────────────

    def _build_search_url(self, page_num: int = 1) -> str:
        base = f"https://www.domain.com.au/sale/{self.suburb_slug}/?excludeunderoffer=1&ssubs=0"
        if page_num == 1:
            return base
        return f"{base}&page={page_num}"

    def _extract_property_count(self, html: str) -> Optional[int]:
        soup = BeautifulSoup(html, 'html.parser')
        for h1 in soup.find_all('h1'):
            m = re.search(r'(\d+)\s+Propert(?:y|ies)\s+for\s+sale', h1.get_text(strip=True), re.IGNORECASE)
            if m:
                return int(m.group(1))
        m = re.search(r'(\d+)\s+Propert(?:y|ies)\s+for\s+sale\s+in', soup.get_text(), re.IGNORECASE)
        if m:
            return int(m.group(1))
        return None

    def _extract_listings(self, html: str):
        """Extract (listing_urls, addresses) from a search-results page.

        Domain migrated the sale-search page OFF __NEXT_DATA__ (2026-07, verified
        live) — the old `"listingUrl":"…"` JSON array no longer exists, which
        silently dropped discovery onto the anchor-href fallback and cost us
        ~20-32% of core-suburb listings (the "listed home shown as off-market"
        incident, 6 Joy Avenue). The authoritative per-page source is now the
        `application/ld+json` array:
          • @type=Residence  → EVERY card's address (count == pageSize, e.g. 20).
                               This is stable across fetches → the completeness yardstick.
          • @type=Event      → auction-listing URLs (a subset).
        Rendered anchors supply the remaining URLs but UNDER-RENDER intermittently
        (4→23 across identical requests), so URLs are a UNION of ld+json Event +
        anchor hrefs; discover() unions these across re-fetches until the URL count
        reaches the Residence count. Listing URLs end in a 7-12 digit id, e.g.
        /23-camberwell-circuit-robina-qld-4226-2020833972.
        """
        urls: set = set()
        addresses: set = set()

        for m in re.finditer(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
        ):
            try:
                arr = json.loads(m.group(1))
            except Exception:
                continue
            for it in (arr if isinstance(arr, list) else [arr]):
                if not isinstance(it, dict):
                    continue
                t = it.get("@type")
                if t == "Residence":
                    nm = (it.get("name") or "").strip()
                    if nm:
                        addresses.add(nm)
                elif t == "Event":
                    u = (it.get("url") or "").replace('\\/', '/').split('?')[0]
                    if re.search(r'-\d{7,12}$', u):
                        urls.add(u if u.startswith('http') else f"https://www.domain.com.au{u}")

        # Supplement URLs from anchor hrefs ending in a listing id (skip search/rent/
        # profile pages). Domain returns absolute or relative hrefs.
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(s in href for s in ('/sale/', '/rent/', '/sold-listings/', '/suburb-profile/')):
                continue
            mm = re.search(r'(/[a-z0-9%-]+-(\d{7,12}))(?:[/?]|$)', href.replace('\\/', '/').split('?')[0])
            if mm:
                urls.add(f"https://www.domain.com.au{mm.group(1)}")

        # Overflow pages (page > totalPages) inject "nearby" listings from other
        # suburbs; keep only URLs whose slug carries THIS suburb (…-burleigh-waters-qld-4220-…)
        # and Residence addresses in THIS suburb, so completeness math stays honest.
        sub = self.suburb_name.lower()
        urls = {u for u in urls if f"-{self.suburb_slug}-" in u}
        addresses = {a for a in addresses if sub in a.lower()}
        return urls, addresses

    def _extract_search_meta(self, html: str) -> Dict[str, Dict]:
        """Per-listing metadata from the search page __NEXT_DATA__ listingsMap —
        currently the displayed price text, keyed by full listing URL. Used to
        refresh existing listings cheaply (price feeds step 115) without a detail
        fetch. The price text here matches the detail-page price for ~90% of
        listings and is fresher where it differs."""
        meta: Dict[str, Dict] = {}
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
        if not m:
            return meta
        try:
            data = json.loads(m.group(1))
        except Exception:
            return meta

        def walk(o):
            if isinstance(o, dict):
                lm = o.get("listingModel")
                if isinstance(lm, dict) and lm.get("url") and "price" in lm:
                    u = lm["url"].replace("\\/", "/").split("?")[0]
                    full = u if u.startswith("http") else f"https://www.domain.com.au{u}"
                    price = (lm.get("price") or "").strip()
                    if price:
                        meta[full] = {"price": price}
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(data)
        return meta

    def discover(self):
        """Phase 1: discover all listing URLs via paginated search.

        Per page we RE-FETCH (up to PAGE_REFETCH_MAX) and union the extracted URLs
        until they cover that page's authoritative ld+json Residence count — Domain
        renders a variable subset of cards per request, so a single fetch routinely
        under-yields. The page's Residence addresses are the completeness target and
        the source of "unresolved" gaps (a listed address whose URL we never got),
        which are surfaced for the coverage-reconciliation / health board.
        """
        self.log("Starting property discovery...")
        all_urls: List[str] = []
        seen = set()
        page_num = 1
        empty_streak = 0

        while page_num <= MAX_PAGES:
            url = self._build_search_url(page_num)

            page_urls: set = set()
            page_addrs: set = set()
            html = None
            for attempt in range(PAGE_REFETCH_MAX):
                html = _fetch(url, retries=5)  # shared helper handles per-request flakiness
                if not html:
                    continue
                if page_num == 1 and self.expected_count is None:
                    self.expected_count = self._extract_property_count(html)
                    if self.expected_count:
                        self.log(f"Expected property count: {self.expected_count}")
                self.search_meta.update(self._extract_search_meta(html))
                u, a = self._extract_listings(html)
                page_urls |= u
                page_addrs |= a
                # Complete once URLs cover this page's declared card count.
                if page_addrs and len(page_urls) >= len(page_addrs):
                    break
                if attempt < PAGE_REFETCH_MAX - 1:
                    time.sleep(BETWEEN_PAGE_DELAY)

            if html is None:
                self.log(f"Page {page_num}: Failed to fetch, stopping pagination")
                break

            new = [u for u in page_urls if u not in seen]
            seen.update(new)
            all_urls.extend(new)
            self.discovered_addresses |= page_addrs
            shortfall = max(0, len(page_addrs) - len(page_urls))
            self.log(
                f"Page {page_num}: {len(page_urls)} urls / {len(page_addrs)} listed "
                f"({len(new)} new, {len(all_urls)} total"
                + (f", {shortfall} unresolved" if shortfall else "") + ")"
            )

            # True end of results: a re-fetched page surfaced no listings at all.
            if not page_addrs and not page_urls:
                break
            # Reached Domain's stated count → done.
            if self.expected_count and len(all_urls) >= self.expected_count:
                break
            # Two CONSECUTIVE pages that add nothing new → end (guards against overflow
            # pages echoing earlier results). A single low-yield page no longer stops us
            # (that was the old truncation bug); the per-page re-fetch has already
            # maximised this page before we judge it "empty".
            if not new:
                empty_streak += 1
                if empty_streak >= 2:
                    break
            else:
                empty_streak = 0

            page_num += 1
            if page_num <= MAX_PAGES:
                time.sleep(BETWEEN_PAGE_DELAY)

        self.discovered_urls = list(dict.fromkeys(all_urls))

        # Addresses Domain lists but we could not resolve to a scrapeable URL — the
        # residual coverage gap even after re-fetching. Keyed by (leading number,
        # street name) via _addr_key so unit/building number runs don't create
        # false gaps regardless of separator style.
        resolved_keys = set()
        for u in self.discovered_urls:
            slug = re.sub(r'-\d{7,12}$', '', u.rstrip('/').split('/')[-1])
            slug = slug.replace(f'-{self.suburb_slug}', '')
            resolved_keys.add(_addr_key(slug))
        self.unresolved_addresses = {
            a for a in self.discovered_addresses if _addr_key(a) not in resolved_keys
        }

        exp = self.expected_count if self.expected_count else "?"
        unres = f", {len(self.unresolved_addresses)} unresolved" if self.unresolved_addresses else ""
        self.log(
            f"Discovery complete: {len(self.discovered_urls)} unique URLs found "
            f"({len(self.discovered_addresses)} listed{unres}, expected {exp})"
        )

    def record_coverage(self):
        """Persist this suburb's discovery outcome to system_monitor.listing_coverage
        so the listing-coverage health board (#1) can show completeness AND the
        SPECIFIC addresses Domain lists that we still don't hold — the signal that
        makes the DB trustworthy enough for the on-market redirect to mean
        something. Best-effort; never raises (must not fail a scrape run)."""
        try:
            sm = self.mongo_client["system_monitor"]
            db_forsale = list(self.collection.find(
                {"listing_status": "for_sale"},
                {"address": 1, "complete_address": 1}))
            db_keys = {_addr_key(d.get("address") or d.get("complete_address") or "")
                       for d in db_forsale}
            # Domain lists it, we don't hold it as for_sale → genuine coverage gap
            # (unresolved URL or a save that failed). This is the actionable list.
            missing = sorted(a for a in self.discovered_addresses
                             if _addr_key(a) not in db_keys)
            sm["listing_coverage"].update_one(
                {"_id": self.collection_name},
                {"$set": {
                    "suburb": self.suburb_name,
                    "postcode": self.postcode,
                    "domain_expected": self.expected_count,
                    "discovered_urls": len(self.discovered_urls),
                    "listed_addresses": len(self.discovered_addresses),
                    "in_db_for_sale": len(db_forsale),
                    "missing_addresses": missing,
                    "missing_count": len(missing),
                    "unresolved_addresses": sorted(self.unresolved_addresses),
                    "updated_at": datetime.utcnow(),
                }},
                upsert=True)
            self.log(f"Coverage recorded: {len(self.discovered_urls)}/"
                     f"{self.expected_count} discovered, {len(db_forsale)} in DB, "
                     f"{len(missing)} missing")
        except Exception as e:
            self.log(f"⚠ Coverage record failed (non-fatal): {e}")

    # ── Phase 2: Detail scraping ───────────────────────────────────────────

    def _extract_address_from_url(self, url: str) -> str:
        """Extract address from Domain URL slug, handling multi-word suburbs."""
        path = url.replace('https://www.domain.com.au/', '').replace('http://www.domain.com.au/', '')
        path = re.sub(r'-\d{7,10}$', '', path)
        parts = path.split('-')
        state_idx = -1
        for i, part in enumerate(parts):
            if part in ('qld', 'nsw', 'vic', 'sa', 'wa', 'tas', 'nt', 'act'):
                state_idx = i
                break
        if state_idx < 1:
            return ' '.join(parts).title()

        state = parts[state_idx].upper()
        postcode_val = parts[state_idx + 1] if state_idx + 1 < len(parts) else ''

        # Try matching multi-word suburbs by checking 3-word, 2-word, then 1-word
        # candidates against the canonical set
        pre_state = parts[:state_idx]  # everything before QLD
        suburb = None
        suburb_words = 0
        for length in (3, 2, 1):
            if len(pre_state) >= length:
                candidate = ' '.join(pre_state[-length:]).lower()
                if candidate in CANONICAL_SUBURBS:
                    suburb = ' '.join(pre_state[-length:]).title()
                    suburb_words = length
                    break
        if not suburb:
            # Fallback: last word before state (original behaviour)
            suburb = pre_state[-1].title() if pre_state else ''
            suburb_words = 1

        street_parts = pre_state[:-suburb_words] if suburb_words <= len(pre_state) else []
        street_address = ' '.join(street_parts).title()
        return f"{street_address}, {suburb}, {state} {postcode_val}"

    def _extract_first_listed_date(self, html: str) -> Dict:
        result = {
            'first_listed_date': None,
            'first_listed_year': None,
            'first_listed_full': None,
            'first_listed_timestamp': None,
            'days_on_domain': None,
            'last_updated_date': None,
        }
        m = re.search(r'"dateListed"\s*:\s*"([^"]+)"', html)
        if m:
            ts = m.group(1)
            result['first_listed_timestamp'] = ts
            try:
                listed = datetime.fromisoformat(ts.replace('Z', '+00:00').split('.')[0])
                result['first_listed_date'] = listed.strftime('%d %B')
                result['first_listed_year'] = listed.year
                result['first_listed_full'] = listed.strftime('%d %B %Y')
                result['days_on_domain'] = (datetime.now() - listed).days
            except Exception:
                pass
        return result

    def _is_invalid_listing(self, property_data: Dict) -> str:
        """Return rejection reason or empty string."""
        address = property_data.get('address', '')
        if not address:
            return 'empty address'
        if re.match(r'^\s*ID:\d+/', address):
            return f'off-plan ID prefix: {address}'
        if re.match(r'^\s*Type\s+[A-Za-z]\b', address, re.IGNORECASE):
            return f'unit type prefix: {address}'
        if re.match(r'^\s*Lot\s+\d+/', address, re.IGNORECASE):
            return f'lot prefix: {address}'
        if re.match(r'^\s*[A-Za-z\s]+,\s*QLD\s+\d{4}\s*[-–]', address):
            return f'no street address: {address}'
        if re.match(r'^\s*[A-Za-z\s]+,\s*QLD\s+\d{4}\s*$', address):
            return f'suburb-only address: {address}'
        return ''

    def scrape_property(self, url: str, idx: int, total: int) -> Optional[Dict]:
        """Fetch and parse a single property page."""
        address_hint = self._extract_address_from_url(url)
        self.log(f"[{idx}/{total}] Scraping: {address_hint}")

        html = _fetch(url, retries=MAX_PROPERTY_RETRIES)
        if not html or len(html) < 500:
            self.log(f"  ✗ Failed to fetch or empty response")
            if FAILURES_LOGGING_ENABLED:
                log_scraping_failure(
                    url=url, suburb=self.suburb_name,
                    error_type="fetch_failed",
                    error_message="curl_cffi returned empty or failed after retries",
                    retry_count=MAX_PROPERTY_RETRIES,
                )
            return None

        # Parse with html_parser
        property_data = parse_listing_html(html, address_hint)
        property_data = clean_property_data(property_data)

        # ── Validate: not a listing page ──
        og_title = property_data.get('og_title', '')
        if og_title:
            og_lower = og_title.lower()
            listing_keywords = [
                'real estate properties for sale',
                'properties for sale in',
                'real estate for sale',
                'property for sale in',
            ]
            if any(kw in og_lower for kw in listing_keywords):
                self.log(f"  ⚠️ SKIPPING: Listing page detected (not individual property)")
                if FAILURES_LOGGING_ENABLED:
                    log_scraping_failure(
                        url=url, suburb=self.suburb_name,
                        error_type="listing_page",
                        error_message=f"Listing page: {og_title[:100]}",
                        retry_count=0,
                    )
                return None

        # ── Extract address from og:title ──
        if og_title:
            og_match = re.search(r'^([^|]+?)\s*\|\s*Domain', og_title)
            if og_match:
                original_address = og_match.group(1).strip()
                formatted_address = re.sub(
                    r'\s+(QLD|NSW|VIC|SA|WA|TAS|NT|ACT)\s+',
                    r', \1 ',
                    original_address,
                )
                property_data['address'] = formatted_address

        # ── Agent extraction from HTML (single pass, no carousel rotation) ──
        soup = BeautifulSoup(html, 'html.parser')
        agents = set()
        agency = None
        agency_elem = soup.find(attrs={'data-testid': 'listing-details__agent-details-agency-name'})
        if agency_elem:
            agency = agency_elem.get_text(strip=True)
        for section in soup.find_all(attrs={'data-testid': 'listing-details__agent-details'}):
            name_elem = section.find(attrs={'data-testid': 'listing-details__agent-details-agent-name'})
            if name_elem:
                name = name_elem.get_text(strip=True)
                if name:
                    agents.add(name)
        if agents:
            agent_list = sorted(agents)
            property_data['agent_names'] = agent_list
            property_data['agent_name'] = ', '.join(agent_list)
        if agency:
            property_data['agency'] = agency

        # ── First listed date ──
        date_info = self._extract_first_listed_date(html)
        property_data.update(date_info)

        # ── Sold detection ──
        sale_mode_match = re.search(r'"saleMode"\s*:\s*"([^"]+)"', html)
        if sale_mode_match and sale_mode_match.group(1).lower() == 'sold':
            property_data['listing_status'] = 'sold'
            self.log(f"  ⚠ Sold listing detected (saleMode=sold)")
        else:
            property_data['listing_status'] = 'for_sale'

        # Defensive: price/address text sold detection
        if property_data['listing_status'] == 'for_sale':
            price_str = property_data.get('price', '') or ''
            addr_str = property_data.get('address', '') or ''
            if re.match(r'^SOLD', price_str, re.IGNORECASE) or re.match(r'^Sold\s', addr_str):
                property_data['listing_status'] = 'sold'
                self.log(f"  ⚠ Sold listing detected (price/address text)")

        # ── Metadata ──
        property_data['listing_url'] = url
        property_data['scrape_mode'] = 'curlffi'
        property_data['extraction_method'] = 'HTML'
        property_data['extraction_date'] = datetime.now().isoformat()
        property_data['source'] = 'curlffi_suburb_scraper'

        # ── Suburb routing (with canonical validation) ──
        actual_suburb = extract_suburb_from_address(property_data.get('address', ''))
        if actual_suburb:
            validated = validate_suburb(actual_suburb)
            if validated:
                property_data['suburb'] = validated
            else:
                # Unrecognised suburb from address — fall back to scrape target
                self.log(f"  ⚠ Unrecognised suburb '{actual_suburb}' — using '{self.suburb_name}'")
                property_data['suburb'] = self.suburb_name
        else:
            property_data['suburb'] = self.suburb_name

        # ── Enrichment fields ──
        property_data['enriched'] = False
        property_data['enrichment_attempted'] = False
        property_data['enrichment_retry_count'] = 0
        property_data['enrichment_error'] = None
        property_data['enrichment_data'] = None
        property_data['last_enriched'] = None
        property_data['image_analysis'] = []

        self.log(f"  ✓ Extracted data from HTML parser")
        return property_data

    # ── MongoDB save ───────────────────────────────────────────────────────

    def save_to_mongodb(self, property_data: Dict) -> bool:
        """Save property using the same upsert logic as the original scraper."""
        try:
            reject_reason = self._is_invalid_listing(property_data)
            if reject_reason:
                self.log(f"  ⛔ REJECTED listing ({reject_reason})")
                return False

            listing_url = property_data['listing_url']

            actual_suburb = property_data.get('suburb', self.suburb_name)
            collection_name = actual_suburb.lower().replace(' ', '_')
            is_target_market = actual_suburb.lower() in TARGET_MARKET_SUBURBS

            target_collection = self.db[collection_name]

            if collection_name != self.collection_name:
                self.log(f"  Routing '{actual_suburb}' → {DATABASE_NAME}.{collection_name}")

            # --- Primary match: listing_url ---
            existing_doc = _mongo_op_with_retry(
                lambda: target_collection.find_one({'listing_url': listing_url})
            )

            # --- Fallback match: GIS complete_address ---
            if existing_doc is None:
                street = property_data.get('street_address', '')
                suburb_val = property_data.get('suburb', actual_suburb)
                postcode_val = property_data.get('postcode', '')
                if street and postcode_val:
                    norm_addr = _normalize_address_for_gis(street, suburb_val, postcode_val)
                    existing_doc = _mongo_op_with_retry(
                        lambda: target_collection.find_one({'complete_address': norm_addr})
                    )
                    if existing_doc:
                        self.log(f"  Matched GIS doc by address: {norm_addr}")

            # --- Sold guard ---
            if property_data.get('listing_status') == 'sold':
                if existing_doc:
                    _mongo_op_with_retry(
                        lambda: target_collection.update_one(
                            {'_id': existing_doc['_id']},
                            {'$set': {'listing_status': 'sold', 'last_updated': datetime.now()}}
                        )
                    )
                    self.log(f"  ⚠ Marked as sold: {property_data.get('address', listing_url)}")
                else:
                    self.log(f"  ⚠ Skipping sold listing (no existing doc): {property_data.get('address', listing_url)}")
                return True

            if existing_doc:
                was_already_for_sale = existing_doc.get('listing_status') == 'for_sale'
                has_blob_images = (
                    was_already_for_sale
                    and existing_doc.get('property_images')
                    and isinstance(existing_doc['property_images'][0], str)
                    and 'blob.core.windows.net' in existing_doc['property_images'][0]
                )

                # Determine which fields to skip
                skip_fields = set(self.PIPELINE_FIELDS)
                if has_blob_images:
                    # Active listing with blob images — preserve them
                    skip_fields |= self.IMAGE_FIELDS
                if was_already_for_sale and existing_doc.get('first_listed_timestamp'):
                    # Preserve original listing date — don't overwrite on re-scrape
                    skip_fields |= {'first_listed_timestamp', 'first_listed_date', 'first_listed_year', 'first_listed_full', 'days_on_domain'}
                update_data = {k: v for k, v in property_data.items() if k not in skip_fields}
                update_data['listing_status'] = 'for_sale'

                # days_on_domain is time-relative — recompute it from the PRESERVED
                # first_listed_timestamp on every re-scrape. It was previously in
                # skip_fields (to protect the original listing date), which froze it
                # at the value set when the listing first entered the DB — so a home
                # listed 130 days ago still showed days_on_domain≈0 (V3-DOM-STALE).
                orig_ts = existing_doc.get('first_listed_timestamp')
                if orig_ts:
                    try:
                        listed = datetime.fromisoformat(str(orig_ts).replace('Z', '+00:00').split('.')[0])
                        if listed.tzinfo is not None:
                            listed = listed.replace(tzinfo=None)
                        update_data['days_on_domain'] = max((datetime.now() - listed).days, 0)
                    except Exception:
                        pass

                # Always store the latest scraped image URLs for reference
                update_data['scraped_property_images'] = property_data.get('property_images', [])
                update_data['scraped_floor_plans'] = property_data.get('floor_plans', [])

                if not was_already_for_sale:
                    # New listing on an existing property — fresh photos taken
                    # Reset blob flag so step 110 re-downloads into a dated folder
                    update_data['images_uploaded_to_blob'] = False
                    self.log(f"  ↻ New listing detected — will re-download images to blob")

                _mongo_op_with_retry(
                    lambda: target_collection.update_one(
                        {'_id': existing_doc['_id']},
                        {'$set': {**update_data, 'last_updated': datetime.now()}}
                    )
                )
                self.log(f"  ✓ Saved to MongoDB (updated)")
                return True
            else:
                property_data['first_seen'] = datetime.now()
                property_data['last_updated'] = datetime.now()
                property_data['listing_status'] = 'for_sale'
                property_data['change_count'] = 0
                property_data['history'] = {}

                if is_target_market:
                    for field in MONITORED_FIELDS:
                        if field in property_data and property_data[field]:
                            property_data['history'][field] = [{
                                'value': property_data[field],
                                'recorded_at': datetime.now(),
                            }]

                _mongo_op_with_retry(
                    lambda: target_collection.insert_one(property_data)
                )
                self.log(f"  ✓ Saved to MongoDB (new)")
                return True

        except Exception as e:
            self.log(f"  [save_to_mongodb] ERROR: {e} | {property_data.get('listing_url', '?')}")
            return False

    # ── Run ─────────────────────────────────────────────────────────────────

    def _refresh_existing(self, url: str, existing: dict) -> bool:
        """Cheap refresh of an already-known for_sale listing: update the displayed
        price (from the search page — feeds step 115 price tracking), recompute
        days_on_domain, and bump last_updated to confirm it's still active. No
        detail fetch. Returns True if the doc was updated."""
        now = datetime.now()
        update = {"last_updated": now}
        new_price = (self.search_meta.get(url) or {}).get("price")
        if new_price and new_price != (existing.get("price") or "").strip():
            update["price"] = new_price
            self.log(f"  ~ price change: {existing.get('price')!r} -> {new_price!r} ({existing.get('address','?')})")
        elif new_price and not existing.get("price"):
            update["price"] = new_price

        # days_on_domain is TIME-RELATIVE and must be recomputed on every run.
        # [DOM-ZERO-STALE] The 2026-07-15 recompute was added to save_to_mongodb(),
        # but the 2026-06-06 incremental change means existing listings never reach
        # that path — they come here instead. Result: the value was written once at
        # insert and frozen, so cards showed "0d listed" on weeks-old homes.
        # first_listed_timestamp is absolute and preserved, so it is the source of truth.
        orig_ts = existing.get("first_listed_timestamp")
        if orig_ts:
            try:
                listed = datetime.fromisoformat(
                    str(orig_ts).replace("Z", "+00:00").split(".")[0])
                if listed.tzinfo is not None:
                    listed = listed.replace(tzinfo=None)
                update["days_on_domain"] = max((now - listed).days, 0)
            except (ValueError, TypeError) as e:
                self.log(f"  [refresh] bad first_listed_timestamp {orig_ts!r}: {e}")
        try:
            _mongo_op_with_retry(lambda: self.collection.update_one(
                {"listing_url": url}, {"$set": update}))
            return True
        except Exception as e:
            self.log(f"  [refresh] ERROR: {e} | {url}")
            return False

    def run(self):
        """Execute discovery + scraping for this suburb.

        Default (incremental): NEW listings are full-detail-scraped; EXISTING
        for_sale listings are refreshed cheaply from the search page (price +
        last_updated) without a detail fetch — ~100x fewer Web Unlocker calls.
        Use full_rescrape=True for a periodic deep refresh of all listings.
        """
        self.log("Starting complete suburb scrape...")

        # Phase 1
        self.discover()

        # Map of existing for_sale listings (url -> doc) for the new-vs-existing split
        existing = {}
        if not self.full_rescrape:
            for d in _mongo_op_with_retry(lambda: list(self.collection.find(
                    {"listing_status": "for_sale", "listing_url": {"$exists": True, "$ne": None}},
                    # first_listed_timestamp is required by _refresh_existing() to
                    # recompute days_on_domain — without it the recompute silently
                    # never fires. See [DOM-ZERO-STALE].
                    {"listing_url": 1, "price": 1, "address": 1,
                     "first_listed_timestamp": 1}))):
                existing[d["listing_url"]] = d

        total = len(self.discovered_urls)
        to_detail = [u for u in self.discovered_urls if self.full_rescrape or u not in existing]
        self.log(f"Scraping: {total} discovered — {len(to_detail)} need detail scrape, "
                 f"{total - len(to_detail)} existing (cheap refresh)")

        for i, url in enumerate(self.discovered_urls, 1):
            if (not self.full_rescrape) and url in existing:
                # Existing listing — cheap refresh, no detail fetch
                if self._refresh_existing(url, existing[url]):
                    self.refreshed += 1
                else:
                    self.failed += 1
                continue

            property_data = self.scrape_property(url, i, total)
            if property_data:
                if self.save_to_mongodb(property_data):
                    self.successful += 1
                else:
                    self.failed += 1
            else:
                self.failed += 1
            time.sleep(BETWEEN_PROPERTY_DELAY)

        self.log(f"Scraping complete: {self.successful} new/scraped, "
                 f"{self.refreshed} refreshed, {self.failed} failed")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="curl_cffi suburb property scraper (Chrome-free)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_curlffi_suburb_scrape.py --suburbs "Robina:4226" "Varsity Lakes:4227"
  python3 run_curlffi_suburb_scrape.py --suburbs "Robina:4226" "Burleigh Waters:4220" "Varsity Lakes:4227"
        """,
    )

    parser.add_argument(
        '--suburbs', nargs='+',
        help='Suburb:Postcode pairs (e.g., "Robina:4226" "Varsity Lakes:4227") or comma-separated names (e.g., "Robina,Varsity Lakes,Burleigh Waters")',
    )
    parser.add_argument('--all', action='store_true', help='Scrape all suburbs from gold_coast_suburbs.json')
    # Kept for CLI compatibility — ignored (no browser to parallelise)
    parser.add_argument('--max-concurrent', type=int, default=1, help=argparse.SUPPRESS)
    parser.add_argument('--parallel-properties', type=int, default=1, help=argparse.SUPPRESS)
    parser.add_argument('--full-rescrape', action='store_true',
                        help='Detail-scrape every listing (default: only new ones; existing refreshed cheaply from search page)')

    args = parser.parse_args()

    # Load suburbs JSON for postcode lookups
    suburbs_json_path = os.path.join(os.path.dirname(__file__), 'gold_coast_suburbs.json')
    postcode_map = {}
    if os.path.exists(suburbs_json_path):
        with open(suburbs_json_path) as f:
            postcode_map = {s['name'].lower(): s['postcode'] for s in json.load(f)['suburbs']}

    # Parse suburb arguments
    suburbs = []
    if args.all:
        suburbs = [(name.title(), pc) for name, pc in postcode_map.items()]
    elif args.suburbs:
        for suburb_arg in args.suburbs:
            # Handle comma-separated names: "Robina,Varsity Lakes,Burleigh Waters"
            if ':' not in suburb_arg and ',' in suburb_arg:
                for name in suburb_arg.split(','):
                    name = name.strip()
                    pc = postcode_map.get(name.lower())
                    if pc:
                        suburbs.append((name, pc))
                    else:
                        print(f"✗ Unknown suburb (no postcode found): {name}")
                        return 1
            elif ':' in suburb_arg:
                name, postcode = suburb_arg.split(':', 1)
                suburbs.append((name.strip(), postcode.strip()))
            else:
                # Single name without colon — look up postcode
                pc = postcode_map.get(suburb_arg.strip().lower())
                if pc:
                    suburbs.append((suburb_arg.strip(), pc))
                else:
                    print(f"✗ Unknown suburb (no postcode found): {suburb_arg}")
                    return 1
    else:
        print("ERROR: Provide --suburbs or --all")
        return 1

    print("\n" + "=" * 80)
    print("CURL_CFFI SUBURB PROPERTY SCRAPER (CHROME-FREE)")
    print("=" * 80)
    print(f"\nSuburbs to process: {len(suburbs)}")
    for name, postcode in suburbs:
        print(f"  - {name} ({postcode})")
    print(f"\nDatabase: {DATABASE_NAME}")
    print(f"Mode: Sequential (curl_cffi with chrome120 TLS impersonation)")
    print("=" * 80 + "\n")

    # Run each suburb sequentially (curl_cffi is fast enough without parallelism)
    results: Dict[str, CurlCffiSuburbScraper] = {}

    for name, postcode in suburbs:
        try:
            scraper = CurlCffiSuburbScraper(name, postcode, full_rescrape=args.full_rescrape)
            scraper.run()
            scraper.record_coverage()  # #1: persist coverage + missing addresses for the health board
            results[name] = scraper
        except Exception as e:
            print(f"[{name}] Fatal error: {e}")

    # ── Final summary ──────────────────────────────────────────────────────

    print("\n" + "=" * 80)
    print("SCRAPING COMPLETE — FINAL SUMMARY")
    print("=" * 80 + "\n")

    for name, postcode in suburbs:
        print(f"\U0001f4ca {name.upper()}")
        if name in results:
            s = results[name]
            print(f"  Expected:  {s.expected_count if s.expected_count is not None else 'N/A'}")
            print(f"  Scraped:   {len(s.discovered_urls)}")
            print(f"  Saved:     {s.successful}")
            print(f"  Failed:    {s.failed}")
        else:
            print(f"  ❌ Error — no results")
        print()

    print("=" * 80 + "\n")

    # Fail loudly if every suburb returned zero discovered URLs.
    # Without this, an Akamai block / proxy outage / DNS issue silently reports
    # "success" to the orchestrator and stale data sits unnoticed (cf. May 2026
    # incident where step 101 reported exit 0 for 2 weeks while delivering 0 URLs).
    total_discovered = sum(len(s.discovered_urls) for s in results.values())
    if total_discovered == 0 and len(suburbs) > 0:
        print(f"❌ FATAL: 0 URLs discovered across all {len(suburbs)} suburbs.")
        print("   Likely cause: upstream block (Akamai), proxy outage, or network issue.")
        print("   Exiting non-zero so the orchestrator/watchdog can surface this.")
        return 2

    # #1: self-registered heartbeat so the listing-coverage board can never fail
    # silently (Rule 7). The per-suburb detail lives in system_monitor.listing_coverage
    # (written by record_coverage above); this single beat proves the reconciliation ran.
    try:
        sys.path.insert(0, '/home/fields/Fields_Orchestrator/scripts')
        from job_status import record_job_result  # type: ignore
        metrics = {}
        worst_gap = 0
        for name, s in results.items():
            exp = s.expected_count or 0
            disc = len(s.discovered_urls)
            gap = max(0, exp - disc)
            worst_gap = max(worst_gap, gap)
            metrics[s.collection_name] = {"expected": exp, "discovered": disc, "gap": gap}
        summary = ", ".join(f"{s.suburb_name} {len(s.discovered_urls)}/{s.expected_count or '?'}"
                            for s in results.values())
        record_job_result(
            "listing_discovery_coverage", "success",
            detail=f"{summary}"[:250],
            cadence_hours=24, title="Listing Discovery Coverage",
            metrics=metrics)
    except Exception as e:
        print(f"[coverage] heartbeat failed (non-fatal): {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
