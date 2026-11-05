"""
Web search engines for Telegram group/channel discovery.
Combines DDGS and Google Search with robust error handling, retry logic,
rate limiting, and improved URL cleaning/deduplication.
"""

import re
import urllib.parse
import time
import random
import logging
from typing import List, Dict, Optional, Any

import requests
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)

# Try to import fake-useragent for dynamic UA rotation, fall back to static list
try:
    from fake_useragent import UserAgent
    USE_FAKE_UA = True
except ImportError:
    USE_FAKE_UA = False
    from ddgs import DDGS

# Default User-Agents fallback list
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Rate limiter state
_request_timestamps = []


def get_headers() -> dict:
    """
    Get request headers with rotated User-Agent.
    Uses fake-useragent if available, otherwise rotates from default list.
    """
    if USE_FAKE_UA:
        try:
            ua = UserAgent()
            user_agent = ua.random
        except Exception:
            user_agent = random.choice(DEFAULT_USER_AGENTS)
    else:
        user_agent = random.choice(DEFAULT_USER_AGENTS)

    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,es-ES;q=0.8,es;q=0.7",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/",
    }


def rate_limit():
    """
    Apply rate limiting to avoid being blocked.
    Ensures at least 1 request per second by default, respecting RATE_LIMIT_PER_MINUTE from config.
    """
    import time as time_module

    now = time_module.time()
    # Keep only timestamps from the last minute
    global _request_timestamps
    _request_timestamps = [ts for ts in _request_timestamps if now - ts < 60]

    # Calculate if we need to wait
    if len(_request_timestamps) >= 30:  # RATE_LIMIT_PER_MINUTE
        wait_time = 60 - (now - _request_timestamps[0]) + 0.1
        if wait_time > 0:
            time_module.sleep(wait_time)

    _request_timestamps.append(time_module.time())


def clean_telegram_url(url: str) -> Optional[str]:
    """
    Cleans and standardizes Telegram URLs.
    Extracts the key part: t.me/joinchat/... or t.me/...
    Handles search engine redirects (DuckDuckGo, Google).
    
    Args:
        url: Raw URL from search results
        
    Returns:
        Cleaned Telegram URL or None if invalid
    """
    try:
        decoded = urllib.parse.unquote(url)

        # Check if it's a search engine redirect link (DuckDuckGo)
        if "duckduckgo.com/l/?kh=-1&uddg=" in decoded:
            match = re.search(r"uddg=([^&]+)", decoded)
            if match:
                decoded = urllib.parse.unquote(match.group(1))

        # Google search redirects
        elif "/url?q=" in decoded or "/url?url=" in decoded:
            match = re.search(r"[?&](q|url)=([^&]+)", decoded)
            if match:
                decoded = urllib.parse.unquote(match.group(2))

        # Standardize protocol and domain
        decoded = re.sub(
            r"https?://(www\.)?(telegram\.(me|dog)|t\.me)/",
            "https://t.me/",
            decoded,
            flags=re.IGNORECASE,
        )

        # Match valid telegram links
        pattern = r"https?://t\.me/(joinchat/[a-zA-Z0-9_\-]+|\+[a-zA-Z0-9_\-]+|[a-zA-Z0-9_]{4,})"
        match = re.match(pattern, decoded, flags=re.IGNORECASE)
        if match:
            matched_url = match.group(0)
            # Remove query parameters if not joinchat or +
            if not matched_url.endswith("joinchat") and "joinchat/" not in matched_url and "+" not in matched_url:
                matched_url = matched_url.split("?")[0]
            return matched_url
    except Exception as e:
        logger.debug(f"Error cleaning URL '{url}': {e}")
    return None


def extract_tme_from_text(text: str) -> set:
    """
    Extracts t.me URLs from any arbitrary text string.
    
    Args:
        text: Text to search for t.me URLs
        
    Returns:
        Set of cleaned Telegram URLs
    """
    urls = set()
    # Match t.me links inside any text
    pattern = r"https?://(?:www\.)?(?:telegram\.(?:me|dog)|t\.me)/(joinchat/[a-zA-Z0-9_\-]+|\+[a-zA-Z0-9_\-]+|[a-zA-Z0-9_]{4,})"
    for m in re.finditer(pattern, text):
        cleaned = clean_telegram_url(m.group(0))
        if cleaned:
            urls.add(cleaned)
    return urls


def _request_with_retry(
    method: str,
    url: str,
    headers: dict,
    params: dict = None,
    cookies: dict = None,
    max_retries: int = 3,
    timeout: int = 15,
    backoff_factor: float = 0.5,
) -> Optional[requests.Response]:
    """
    Make a request with exponential backoff retry logic.
    
    Args:
        method: HTTP method (GET, POST)
        url: Request URL
        headers: Request headers
        params: Query parameters
        cookies: Cookie dictionary
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        backoff_factor: Base factor for exponential backoff
        
    Returns:
        Response object or None if all retries failed
    """
    for attempt in range(max_retries + 1):
        try:
            rate_limit()  # Apply rate limiting
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                cookies=cookies,
                timeout=timeout,
            )

            # Check if we got a successful response
            if response.status_code == 200:
                return response

            # Handle rate limiting (429) or temporary errors
            if response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                wait_time = backoff_factor * (2 ** attempt) + random.uniform(0.1, 0.5)
                logger.warning(
                    f"Request returned status {response.status_code}. "
                    f"Retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries + 1})"
                )
                time.sleep(wait_time)
                continue

            # For other errors, return the response anyway
            logger.warning(f"Request failed with status {response.status_code}")
            return response

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                wait_time = backoff_factor * (2 ** attempt) + random.uniform(0.1, 0.5)
                logger.warning(f"Timeout on attempt {attempt + 1}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries + 1} attempts timed out for {url}")

        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                wait_time = backoff_factor * (2 ** attempt) + random.uniform(0.1, 0.5)
                logger.warning(f"Request error: {e}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"All retries failed: {e}")

    return None


def search_ddgs(query: str, max_results: int = 30) -> List[Dict[str, Any]]:
    """
    Uses the duckduckgo-search Python library (DDGS) which handles
    anti-bot measures internally. Most reliable engine for Telegram dorking.
    
    Args:
        query: Search query (will be prefixed with 'site:t.me')
        max_results: Maximum number of results to return
        
    Returns:
        List of result dictionaries with url, title, snippet, source
    """
    results = []
    seen_urls = set()

    full_query = f"site:t.me {query}"

    try:
        with DDGS() as ddgs:
            for r in ddgs.text(full_query, max_results=max_results):
                try:
                    href = r.get("href", "")
                    title = r.get("title", "")
                    body = r.get("body", "")

                    cleaned_url = clean_telegram_url(href)

                    # Also try to extract t.me links from the title/body text
                    if not cleaned_url:
                        text_urls = extract_tme_from_text(href + " " + title + " " + body)
                        if text_urls:
                            cleaned_url = text_urls.pop()

                    if cleaned_url and cleaned_url not in seen_urls:
                        seen_urls.add(cleaned_url)
                        results.append({
                            "url": cleaned_url,
                            "title": title or cleaned_url.split("/")[-1],
                            "snippet": body or "Enlace encontrado en DuckDuckGo",
                            "source": "DuckDuckGo"
                        })

                    if len(results) >= max_results:
                        break
                except Exception as e:
                    logger.debug(f"Error processing DDGS result: {e}")
                    continue
    except Exception as e:
        logger.error(f"DDGS search failed: {e}")

    return results


def search_google(
    query: str, max_results: int = 30, use_proxy: bool = False
) -> List[Dict[str, Any]]:
    """
    Scrapes Google Search with GDPR cookie bypass and retry logic.
    Includes optional proxy support and enhanced error handling.
    
    Args:
        query: Search query (will be prefixed with 'site:t.me')
        max_results: Maximum number of results to return
        use_proxy: Whether to attempt proxy usage (currently logged, not fully implemented)
        
    Returns:
        List of result dictionaries
    """
    results = []
    seen_urls = set()

    full_query = f"site:t.me {query}"

    url = "https://www.google.com/search"
    params = {
        "q": full_query,
        "num": max_results,
    }

    cookies = {
        "CONSENT": "YES+cb.20231205-09-p0.es+FX+907",
        "SOCS": "CoYBOgB4bGNfc2Vzc2lvbl9pZBoSZ21haWwuY29tEgdjb25zZW50IAE",
    }

    headers = get_headers()
    headers["Referer"] = "https://www.google.com/"

    # Attempt request with retry logic
    response = _request_with_retry(
        method="GET",
        url=url,
        headers=headers,
        params=params,
        cookies=cookies,
        max_retries=3,
        timeout=15,
    )

    if not response or response.status_code != 200:
        logger.warning(f"Google search failed: status {response.status_code if response else 'no response'}")
        return results

    try:
        soup = BeautifulSoup(response.text, "lxml")

        links = soup.select("a")
        for link in links:
            try:
                href = link.get("href", "")
                title = link.get_text(strip=True)

                cleaned_url = clean_telegram_url(href)
                if not cleaned_url and "t.me" in title:
                    cleaned_url = clean_telegram_url(title)

                if cleaned_url and cleaned_url not in seen_urls:
                    # Extract snippet from parent elements
                    snippet = ""
                    parent = link.find_parent()
                    for _ in range(6):  # Increased from 4 for better snippet extraction
                        if not parent:
                            break
                        # Try various snippet class names
                        snippet_elem = parent.select_one(
                            ".VwiC3b, .MUbC5d, .yDty9e, .GAsGB, .Z26q7c"
                        )
                        if snippet_elem:
                            snippet = snippet_elem.get_text(strip=True)
                            break
                        parent = parent.find_parent()

                    seen_urls.add(cleaned_url)
                    results.append({
                        "url": cleaned_url,
                        "title": title if title and "t.me" not in title else cleaned_url.split("/")[-1],
                        "snippet": snippet or "Enlace encontrado en Google",
                        "source": "Google"
                    })

                    if len(results) >= max_results:
                        break
            except Exception as e:
                logger.debug(f"Error processing Google link: {e}")
                continue
    except Exception as e:
        logger.error(f"Error parsing Google search results: {e}")

    return results[:max_results]


def search_hybrid_web(query: str, max_results: int = 30) -> List[Dict[str, Any]]:
    """
    Hybrid search: tries the DDGS library first (most reliable),
    then Google as a fallback. Combines results and removes duplicates.
    
    Implements proper rate limiting between engine calls and
    intelligent deduplication based on URL + title fingerprint.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        Combined list of unique results from all available engines
    """
    combined_results = []
    seen_urls = set()
    seen_fingerprints = set()  # For better dedup: URL + title combination

    # 1. Try DDGS library (most reliable)
    ddgs_res = search_ddgs(query, max_results)
    for r in ddgs_res:
        try:
            url = r.get("url", "")
            title = r.get("title", "")
            if url:
                # Create fingerprint for better dedup
                fingerprint = f"{url}|{title.lower()[:50] if title else ''}"
                if url not in seen_urls and fingerprint not in seen_fingerprints:
                    seen_urls.add(url)
                    seen_fingerprints.add(fingerprint)
                    combined_results.append(r)
        except Exception as e:
            logger.debug(f"Error adding DDGS result: {e}")
            continue

    # 2. If we need more results, try Google
    if len(combined_results) < max_results:
        # Respectful delay between engines
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)
        google_res = search_google(query, max_results - len(combined_results))
        for r in google_res:
            try:
                url = r.get("url", "")
                title = r.get("title", "")
                if url:
                    fingerprint = f"{url}|{title.lower()[:50] if title else ''}"
                    if url not in seen_urls and fingerprint not in seen_fingerprints:
                        seen_urls.add(url)
                        seen_fingerprints.add(fingerprint)
                        combined_results.append(r)
            except Exception as e:
                logger.debug(f"Error adding Google result: {e}")
                continue

    # Return up to max_results, but shuffle slightly to mix sources
    final_results = combined_results[:max_results]
    
    # Simple shuffle to mix DDGS and Google results if we have enough
    if len(final_results) > 5:
        random.shuffle(final_results)
    
    return final_results


def parse_telegram_preview(url: str) -> dict:
    """
    Fetches the public t.me page and extracts metadata.
    Does NOT require a Telegram account or API credentials.
    
    Enhanced with:
    - Retry logic with backoff
    - Better error classification
    - More robust element detection
    - Additional metadata extraction
    - Non-breaking space handling
    
    Args:
        url: Telegram group/channel URL (t.me/... or t.me/joinchat/...)
        
    Returns:
        Dictionary with validation metadata including:
        - valid: bool
        - title: str
        - description: str
        - type: str (Grupo, Canal, Bot, etc.)
        - members: int or None
        - online: int or None
        - username: str or None
        - invite_hash: str or None
        - url: str
        - error: str or None
    """
    rate_limit()  # Apply rate limiting
    
    # Ensure URL is properly formatted
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Clean the URL first
    cleaned_url = clean_telegram_url(url)
    if not cleaned_url:
        return {
            "valid": False,
            "error": "No se pudo limpiar la URL",
            "title": "",
            "description": "",
            "type": "Desconocido",
            "members": None,
            "online": None,
            "username": None,
            "invite_hash": None,
            "url": url,
        }

    # Use enhanced retry request
    headers = get_headers()
    
    response = _request_with_retry(
        method="GET",
        url=cleaned_url,
        headers=headers,
        timeout=20,
        max_retries=2,
        backoff_factor=1.0,
    )

    if not response:
        return {
            "valid": False,
            "error": "No se pudo conectar con la página",
            "title": "",
            "description": "",
            "type": "Desconocido",
            "members": None,
            "online": None,
            "username": None,
            "invite_hash": None,
            "url": cleaned_url,
        }

    if response.status_code != 200:
        return {
            "valid": False,
            "error": f"HTTP {response.status_code}",
            "title": "",
            "description": "",
            "type": "Desconocido",
            "members": None,
            "online": None,
            "username": None,
            "invite_hash": None,
            "url": cleaned_url,
        }

    try:
        soup = BeautifulSoup(response.text, "lxml")

        # Initialize result variables
        title = "Sin Título"
        description = "Sin descripción"
        chat_type = "Desconocido"
        member_count = None
        online_count = None
        username = None
        invite_hash = None

        # Check for valid chat/link using multiple selectors
        # Priority: .tgme_page_title > .tgme_channel_info_header_title > <head title>
        title_elem = soup.select_one(".tgme_page_title, .tgme_channel_info_header_title")
        if title_elem:
            title = title_elem.get_text(strip=True)
        else:
            head_title = soup.select_one("head title")
            if head_title:
                head_text = head_title.get_text(strip=True)
                # Filter out Telegram generic titles
                if "Telegram" in head_text and "Contact" not in head_text:
                    # It might be a download page or other non-chat page
                    if "download" in response.text.lower():
                        return {
                            "valid": False,
                            "error": "Página de descarga / No es un chat/channel",
                            "title": "",
                            "description": "",
                            "type": "Desconocido",
                            "members": None,
                            "online": None,
                            "username": None,
                            "invite_hash": None,
                            "url": cleaned_url,
                        }
                title = head_text if head_text else "Sin Título"

        # Extra details (members, subscribers, online count)
        extra_elem = soup.select_one(
            ".tgme_page_extra, .tgme_channel_info_subscriber_count, .tgme_chat_info"
        )
        extra_text = extra_elem.get_text(strip=True) if extra_elem else ""

        # Description
        desc_elem = soup.select_one(
            ".tgme_page_description, .tgme_channel_info_description, .tgme_chat_description"
        )
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        else:
            # Try to get description from meta tags
            meta_desc = soup.select_one('meta[name="description"]')
            if meta_desc:
                description = meta_desc.get("content", "Sin descripción")

        # Standardize extra text (replace non-breaking spaces and normalize)
        clean_extra = extra_text.replace("\xa0", " ").replace("  ", " ").lower()

        # Determine chat type based on extra_text patterns
        if "members" in clean_extra or "miembros" in clean_extra:
            chat_type = "Grupo"
            match = re.search(r"(\d+(?:\s?\d{3})*)(members|miembros)", clean_extra, re.IGNORECASE)
            if match:
                # Clean the matched number (remove spaces)
                num_str = match.group(1).replace(" ", "").replace("\xa0", "")
                try:
                    member_count = int(num_str)
                except ValueError:
                    pass
            
            # Check for online count
            online_match = re.search(r"(\d+)\s*(online|enlínea|en línea)", clean_extra, re.IGNORECASE)
            if online_match:
                try:
                    online_count = int(online_match.group(1))
                except ValueError:
                    pass

        elif "subscribers" in clean_extra or "suscriptores" in clean_extra:
            chat_type = "Canal"
            match = re.search(r"(\d+(?:\s?\d{3})*)(subscribers|suscriptores)", clean_extra, re.IGNORECASE)
            if match:
                num_str = match.group(1).replace(" ", "").replace("\xa0", "")
                try:
                    member_count = int(num_str)
                except ValueError:
                    pass

        elif "bot" in cleaned_url.lower() or "bot" in clean_extra:
            chat_type = "Bot"

        else:
            # Try to determine type from action button
            view_button = soup.select_one(".tgme_action_button_new, .tgme_button")
            if view_button:
                btn_text = view_button.get_text(strip=True).lower()
                if "send message" in btn_text or "enviar mensaje" in btn_text:
                    chat_type = "Usuario/Bot"
                elif "join" in btn_text or "unirse" in btn_text or "unir" in btn_text:
                    chat_type = "Grupo/Canal"
                elif "view" in btn_text or "ver" in btn_text:
                    chat_type = "Público"
            else:
                # Default if can't determine
                chat_type = "Desconocido"

        # Extract direct username or join hash from URL
        if "/joinchat/" in cleaned_url:
            invite_hash = cleaned_url.split("/joinchat/")[-1]
            # Take only the hash part (before any ? or &)
            invite_hash = invite_hash.split("?")[0].split("&")[0]
        elif "/+" in cleaned_url:
            invite_hash = cleaned_url.split("/+")[-1]
            invite_hash = invite_hash.split("?")[0].split("&")[0]
        else:
            # It's a username-based URL
            username = cleaned_url.split("/")[-1]
            username = username.split("?")[0].split("&")[0]
            # If it's just a short username, validate it looks reasonable
            if username and len(username) > 3:
                # Check if it looks like a valid t.me username pattern
                if re.match(r"^[a-zA-Z0-9_]{5,32}$", username):
                    pass  # Valid username format

        return {
            "valid": True,
            "title": title,
            "description": description,
            "type": chat_type,
            "members": member_count,
            "online": online_count,
            "extra_info": extra_text,
            "username": username,
            "invite_hash": invite_hash,
            "url": cleaned_url,
        }

    except Exception as e:
        logger.error(f"Error parsing telegram preview for {url}: {e}", exc_info=True)
        return {
            "valid": False,
            "error": f"Error de análisis: {str(e)[:100]}",
            "title": "",
            "description": "",
            "type": "Desconocido",
            "members": None,
            "online": None,
            "username": None,
            "invite_hash": None,
            "url": url if url else cleaned_url,
        }