# ⚡ sc_tel: Premium Telegram Group Searcher in Terminal ⚡

An advanced interactive Python script for searching and validating Telegram groups, supergroups, and channels on any theme, using a hybrid strategy: **Web Scraping/Dorking** and **Telegram Client API (Telethon)**.

---

## Key Features

1. **Hybrid Web Search (No Credentials Required):**
   * Performs intelligent dorking searches on search engines to collect Telegram links (`t.me/...` or `t.me/joinchat/...`).
   * No API configuration or Telegram account required for initial search.
2. **Real-Time Web Validation:**
   * Automatically extracts real titles, descriptions, and member counts from Telegram preview pages.
   * Respectful of server limits during scraping.
3. **Optional Telegram API Validation (Telethon):**
   * Direct integration with the official Telegram API (`api_id` and `api_hash`).
   * Validates invitation links (`joinchat` and `+`) without joining them to get precise private/group details.
   * Performs native global searches directly within Telegram's database (`contacts.SearchRequest`).
4. **Spectacular CLI Interface:**
   * High-definition colored tables in the terminal using the `rich` library.
   * Interactive progress bars and spinners.
   * Dynamic filters to search only **Channels** or **Groups**.
5. **Flexible Export:**
   * Instantly export results to structured files **CSV**, **JSON**, or **Markdown**.

---

## Installation Requirements

The script uses a Python virtual environment. You can install and set it up with the following commands:

```bash
# Navigate to the directory
cd /home/bender/Descargas/sc_tel

# Make sure the virtual environment is active
source busq_grup_tel/bin/activate

# Install dependencies (already performed during initialization)
pip install -r requirements.txt
```

---

## Usage Guide

Run the script using `python cli.py` followed by the search keyword.

### 1. Basic Quick Search
Searches for groups/channels on a theme. Returns links found on the web:
```bash
python cli.py "python programming"
```

### 2. Web Validation Search (Without Telegram API)
Get metadata like chat title, member count, and type by scraping the `t.me` preview page:
```bash
python cli.py "cryptocurrency" --validate
```

### 3. Type Filter Search
Filter to view only groups or only channels:
```bash
# Show only groups
python cli.py "musica" --validate --groups

# Show only channels
python cli.py "noticias" --validate --channels
```

### 4. Export Results
Save results directly to a structured format (`.csv`, `.json`, or `.md`):
```bash
python cli.py "artificial intelligence" --validate --output resultados.csv
```

### 5. Advanced Mode (Deep Validation and Native Search)
Use your Telegram account to check private invitation links and search natively in the Telegram network:
```bash
python cli.py "cybersecurity" --api
```
*The first time you use the `--api` parameter, the script will ask for your `api_id` and `api_hash` from [my.telegram.org](https://my.telegram.org) and will create a safe session on your machine. You will be optionally asked to save the credentials in `config.json` so you don't have to type them again.*

---

## Available Options in the Console

| Option | Short Command | Description |
| --- | --- | --- |
| `--max-results` | `-n` | Maximum number of results to search (default: 30). |
| `--validate` | `-v` | Validates `t.me` web pages to extract titles and member counts in real time. |
| `--api` | `-a` | Connects to the Telegram API using Telethon (native search and invitation validation). |
| `--output` | `-o` | Saves results to a file (`.json`, `.csv`, `.md`). |
| `--groups` | | Filters and shows only Telegram groups. |
| `--channels` | | Filters and shows only Telegram channels. |

---

## Credits and Style

Developed with ❤️ to offer a premium interactive experience in Linux environments. Designed with dark HSL palettes and glassmorphism visual in modern terminals.