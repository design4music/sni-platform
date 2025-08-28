# Domain Profiles

This directory contains domain-specific extraction profiles for sites that need custom selectors.

## Profile Format

Each profile is a JSON file named after the domain (e.g., `timesofindia.indiatimes.com.json`):

```json
{
  "main_selector": ".article-content",
  "remove_selectors": [
    ".advertisement",
    ".social-share",
    ".related-articles"
  ],
  "notes": "Optional description of domain-specific issues"
}
```

## When to Use

Create profiles for domains where:
1. Trafilatura fails to extract content properly
2. Standard extraction gets too much boilerplate
3. Content is hidden behind specific selectors

## Examples

- `timesofindia.indiatimes.com.json` - For Times of India articles
- `scmp.com.json` - For South China Morning Post (if needed)