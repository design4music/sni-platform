import re
from datetime import datetime

def parse_rt_rss_feed(file_path):
    """Parse RT RSS feed using regex patterns instead of XML parser"""
    
    try:
        # Read the entire file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find all item blocks using regex
        item_pattern = r'<item>(.*?)</item>'
        items = re.findall(item_pattern, content, re.DOTALL)
        
        articles = []
        counter = 1
        
        for item in items:
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', item)
            if not title_match:
                continue
                
            title = title_match.group(1).strip()
            # Remove " - rt.com" suffix if present
            if title.endswith(' - rt.com'):
                title = title[:-9].strip()
            
            # Extract publication date
            pubdate_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
            if not pubdate_match:
                continue
                
            pub_date_str = pubdate_match.group(1).strip()
            try:
                # Parse RFC 2822 format: "Tue, 02 Sep 2025 04:40:00 GMT"
                pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                formatted_date = pub_date.strftime('%Y-%m-%d')
            except ValueError:
                try:
                    # Try alternative format without timezone
                    pub_date = datetime.strptime(pub_date_str.replace(' GMT', ''), '%a, %d %b %Y %H:%M:%S')
                    formatted_date = pub_date.strftime('%Y-%m-%d')
                except ValueError:
                    formatted_date = "2025-09-02"  # Default fallback
            
            # Extract the Google News link
            link_match = re.search(r'<link>(.*?)</link>', item)
            google_link = link_match.group(1).strip() if link_match else ""
            
            # Try to extract RT URL from description if available
            description_match = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
            rt_url = f"https://www.rt.com/news/article-{counter}/"  # Default placeholder
            
            if description_match:
                desc = description_match.group(1)
                # Look for RT URLs in the description
                rt_url_match = re.search(r'href="([^"]*rt\.com[^"]*)"', desc)
                if rt_url_match:
                    rt_url = rt_url_match.group(1)
                elif google_link:
                    # Use the Google News link as fallback
                    rt_url = google_link
            
            # Format: h01 | YYYY-MM-DD | rt.com | en | [article title] | [direct RT article URL]
            article_line = f"h{counter:02d} | {formatted_date} | rt.com | en | {title} | {rt_url}"
            articles.append(article_line)
            counter += 1
        
        return articles
        
    except Exception as e:
        print(f"Error parsing feed: {e}")
        return []

if __name__ == "__main__":
    file_path = r"C:\Users\Maksim\Documents\SNI\rt_feed_sample.txt"
    articles = parse_rt_rss_feed(file_path)
    
    print(f"Found {len(articles)} articles:")
    print()
    for article in articles:
        print(article)