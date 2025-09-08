import re
from datetime import datetime
import html

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
    
    # Write to output file with UTF-8 encoding
    with open('C:/Users/Maksim/Documents/SNI/euronews_articles_output.txt', 'w', encoding='utf-8') as f:
        for article in articles:
            f.write(article + '\n')
        f.write(f'\nTotal articles found: {len(articles)}\n')
    
    print(f"Extracted {len(articles)} articles")
    print("First 10 articles:")
    for i, article in enumerate(articles[:10]):
        print(article)
    
    if len(articles) > 10:
        print(f"... ({len(articles) - 10} more articles)")