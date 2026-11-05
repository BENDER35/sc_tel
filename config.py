"""
Configuration module for sc_tel.

Manages settings, API credentials, and configurable parameters.
Supports environment variables and optional encrypted config.
"""

import os
import json
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()

# Search engine settings
SEARCH_MAX_RESULTS = int(os.getenv("SC_TEL_MAX_RESULTS", "30"))
SEARCH_TIMEOUT = int(os.getenv("SC_TEL_SEARCH_TIMEOUT", "15"))
SEARCH_DELAY_MIN = float(os.getenv("SC_TEL_DELAY_MIN", "0.5"))
SEARCH_DELAY_MAX = float(os.getenv("SC_TEL_DELAY_MAX", "2.0"))

# Validation settings
VALIDATION_TIMEOUT = int(os.getenv("SC_TEL_VALIDATION_TIMEOUT", "10"))
VALIDATION_RETRY_COUNT = int(os.getenv("SC_TEL_VALIDATION_RETRY", "2"))
VALIDATION_DELAY_MIN = float(os.getenv("SC_TEL_VALIDATION_DELAY_MIN", "0.5"))
VALIDATION_DELAY_MAX = float(os.getenv("SC_TEL_VALIDATION_DELAY_MAX", "1.5"))

# Telegram API settings
TELEGRAM_API_ID = os.getenv("TG_API_ID")
TELEGRAM_API_HASH = os.getenv("TG_API_HASH")
TELEGRAM_PHONE = os.getenv("TG_PHONE")

# Output settings
OUTPUT_DEFAULT_FORMAT = os.getenv("SC_TEL_OUTPUT_FORMAT", "markdown")

# Rate limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv("SC_TEL_RATE_LIMIT", "30"))

# Feature flags
ENABLE_CACHING = os.getenv("SC_TEL_ENABLE_CACHING", "true").lower() == "true"
ENABLE_PROXY = os.getenv("SC_TEL_ENABLE_PROXY", "false").lower() == "true"


def load_config():
    """Load configuration from config.json if it exists."""
    config_file = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # Merge with environment defaults (config.json overrides env)
                return {**get_default_config(), **user_config}
        except Exception as e:
            print(f"[warning]No se pudo cargar config.json: {e}")
    return get_default_config()


def get_default_config():
    """Get default configuration values."""
    return {
        "api_id": TELEGRAM_API_ID,
        "api_hash": TELEGRAM_API_HASH,
        "phone": TELEGRAM_PHONE,
    }


def save_config(api_id, api_hash):
    """Save API credentials to config.json."""
    config_file = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"api_id": api_id, "api_hash": api_hash}, f, indent=4)
        print(f"[success]✓[/success] Credenciales de Telegram guardadas en `config.json` para futuros usos.")
    except Exception as e:
        print(f"[warning]![/warning] No se pudo guardar config.json: {e}")


def get_api_credentials():
    """Get API credentials prioritizing environment variables, then config.json."""
    config = load_config()
    api_id = os.environ.get("TG_API_ID") or config.get("api_id")
    api_hash = os.environ.get("TG_API_HASH") or config.get("api_hash")
    return api_id, api_hash


def get_rate_limiter():
    """Get a rate limiter function based on configuration."""
    last_call = [0]
    
    def rate_limit():
        import time
        elapsed = time.time() - last_call[0]
        min_delay = RATE_LIMIT_PER_MINUTE / 60.0
        if elapsed < min_delay:
            import time as time_module
            time_module.sleep(min_delay - elapsed)
        last_call[0] = time.time()
    
    return rate_limit