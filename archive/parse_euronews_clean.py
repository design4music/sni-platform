import re
from datetime import datetime
import html
import unicodedata

def clean_text(text):
    """Clean text by removing problematic Unicode characters"""
    if not text:
        return text
    
    # Normalize Unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Replace common problematic characters
    replacements = {
        '\u010d': 'c',  # č
        '\u00ed': 'i',  # í
        '\u00e1': 'a',  # á
        '\u2013': '-',  # en dash
        '\u2014': '-',  # em dash
        '\u2018': "'",  # left single quote
        '\u2019': "'",  # right single quote
        '\u201c': '"',  # left double quote
        '\u201d': '"',  # right double quote
        '\u00a0': ' ',  # non-breaking space
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove any remaining non-ASCII characters
    text = text.encode('ascii', errors='ignore').decode('ascii')
    
    return text

def parse_euronews_feed(file_path):
    # Read the file with proper encoding handling
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all <item> blocks using regex
    item_pattern = r'<item>(.*?)</item>'
    items = re.findall(item_pattern, content, re.DOTALL)

    articles = []
    counter = 1

    for item in items:
        # Extract title
        title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item, re.DOTALL)
        if title_match:
            title = title_match.group(1) if title_match.group(1) else title_match.group(2)
            title = html.unescape(title.strip()) if title else 'Unknown Title'
        else:
            title = 'Unknown Title'
        
        # Extract link
        link_match = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
        link = link_match.group(1).strip() if link_match else 'Unknown Link'
        
        # Extract publication date
        pubdate_match = re.search(r'<pubDate>(.*?)</pubDate>', item, re.DOTALL)
        pubdate = pubdate_match.group(1).strip() if pubdate_match else 'Unknown Date'
        
        # Clean up title (remove ' - Euronews.com' suffix if present)
        if title.endswith(' - Euronews.com'):
            title = title[:-16]
        
        # Clean the title of problematic characters
        title = clean_text(title)
        
        # Convert pubDate to YYYY-MM-DD format
        try:
            date_obj = datetime.strptime(pubdate, '%a, %d %b %Y %H:%M:%S %Z')
            formatted_date = date_obj.strftime('%Y-%m-%d')
        except:
            # Try alternative format or leave as unknown
            formatted_date = 'UNKNOWN'
        
        # Format the output
        article_line = f'h{counter:02d} | {formatted_date} | euronews.com | en | {title} | {link}'
        articles.append(article_line)
        counter += 1

    return articles

if __name__ == "__main__":
    file_path = 'C:/Users/Maksim/Documents/SNI/euronews_feed_sample.txt'
    articles = parse_euronews_feed(file_path)
    
    # Print all articles directly
    for article in articles:
        print(article)
    
    print()
    print(f"Total articles found: {len(articles)}")