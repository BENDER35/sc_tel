# 📚 sc_tel: English Didactic Guide

## Welcome to sc_tel

sc_tel is an advanced Telegram groups and channels searcher that works directly from your terminal. This guide will teach you how to take advantage of all its features, from basic searches to deep validation with the Telegram API.

---

## 🔍 Level 1: Basic Searches (No Credentials Required)

### Goal
Learn to search for Telegram groups and channels simply with a keyword, without needing to configure credentials.

### What will you learn?
- Quick searches with keywords
- How to filter results by type (groups/channels)
- Basic CLI commands

### Practical Exercise 1
```bash
# Search for groups about "python programming"
python cli.py "python programming"

# Search for channels about "news"
python cli.py "news" --channels
```

### Practical Exercise 2
```bash
# Web validation search (without API)
python cli.py "cryptocurrency" --validate
```

---

## 🎛️ Level 2: Filters and Advanced Options

### Goal
Master the available filters and options to refine your searches.

### What will you learn?
- Filter only groups (`--groups`)
- Filter only channels (`--channels`)
- Limit the number of results (`--max-results` or `-n`)
- Combine options for specific searches

### Practical Exercise 3
```bash
# Show only groups about "musik"
python cli.py "musik" --validate --groups

# Show only channels about "technology" with a limit of 10 results
python cli.py "technology" --validate --channels --max-results 10
```

### Practical Exercise 4
```bash
# Export results to CSV
python cli.py "artificial intelligence" --validate --output mis_grupos.csv
```

---

## 🔐 Level 3: Telegram API Mode (Deep Validation)

### Goal
Use your Telegram account to get more precise details and native search.

### What will you learn?
- How to get your credentials at my.telegram.org
- Configure `api_id` and `api_hash`
- Native search in Telegram's database
- Validate invitation links without joining them

### First Steps with the API
1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your Telegram account
3. Get your `api_id` and `api_hash`
4. Run: `python cli.py "your_search" --api`
5. When prompted, enter your credentials
6. Optionally, save them in `config.json`

### Practical Exercise 5
```bash
# Native search with API
python cli.py "cybersecurity" --api

# Invitation link validation
python cli.py "https://t.me/joinhash123" --api
```

---

## 📁 Level 4: Export and Data Analysis

### Goal
Learn to export and analyze the obtained results.

### Supported Formats
- **CSV**: For analysis in Excel or Python/pandas
- **JSON**: For data processing with analytical tools
- **Markdown**: For formatted documentation or sharing

### Practical Exercises
```bash
# Export to CSV
python cli.py "python" --validate --output my_results.csv

# Export to JSON
python cli.py "python" --validate --output my_results.json

# Export to Markdown
python cli.py "python" --validate --output my_results.md
```

### Quick Analysis with Python
After exporting to CSV, you can analyze the data:
```python
import csv

with open('my_results.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"Title: {row['Title / Name']}")
        print(f"Type: {row['Type']}")
        print(f"Members: {row['Members']}")
        print("---")
```

---

## ⚠️ Tips and Best Practices

### For Better Results
1. **Use specific keywords**: Instead of "python", try "python programming" or "python learning"
2. **Combine validation and filters**: `python cli.py "python" --validate --groups`
3. **Respect limits**: The script has automatic delays to avoid overloading servers
4. **Use the API when you need precision**: For private group details or exact counts

### Common Issues
- **No results found**: Try different keywords or reduce the number of results
- **Connection errors**: The script has automatic retries, but if it persists, check your internet connection
- **Flood wait**: If you use the API frequently, Telegram may rate-limit you. Wait the suggested time and try again

---

## 🚀 Quick Shortcuts and Tips

| Command | Effect |
| --- | --- |
| `python cli.py "text"` | Quick basic search |
| `python cli.py "text" --validate` | With web metadata validation |
| `python cli.py "text" --api` | With native Telegram API |
| `python cli.py "text" --groups` | Only groups |
| `python cli.py "text" --channels` | Only channels |
| `python cli.py "text" -n 5` | Maximum 5 results |
| `python cli.py "text" -o .md` | Export to Markdown |

---

## 🚀 Where to Get Help?

- **Documentation**: Check the `MEJORAS_APLICADAS.md` file for technical improvements
- **Reports**: If you find bugs, check `searcher.log` generated in the directory
- **Updates**: The script receives periodic improvements; check `git pull` for the latest version

---

*Developed with ❤️ to offer a premium interactive experience in Linux environments. Designed with dark HSL palettes and glassmorphism visual in modern terminals.*