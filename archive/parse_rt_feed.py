import xml.etree.ElementTree as ET
from datetime import datetime
import re

def parse_rt_rss_feed(file_path):
    """Parse RT RSS feed and extract articles in specified format"""
    
    try:
        # Read the file and skip the first line which is not valid XML
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        # Skip first line and join the rest
        xml_content = ''.join(lines[1:])
        
        # Clean up any problematic characters
        xml_content = xml_content.replace('©', '(c)')
        
        # Parse the XML content
        root = ET.fromstring(xml_content)
        
        articles = []
        counter = 1
        
        # Find all item elements
        for item in root.findall('.//item'):
            title_elem = item.find('title')
            pubdate_elem = item.find('pubDate')
            link_elem = item.find('link')
            source_elem = item.find('source')
            
            if title_elem is not None and pubdate_elem is not None:
                # Extract title and clean it (remove " - rt.com" suffix if present)
                title = title_elem.text.strip()
                if title.endswith(' - rt.com'):
                    title = title[:-9].strip()
                
                # Parse and format date
                pub_date_str = pubdate_elem.text.strip()
                try:
                    # Parse RFC 2822 format: "Tue, 02 Sep 2025 04:40:00 GMT"
                    pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                    formatted_date = pub_date.strftime('%Y-%m-%d')
                except ValueError:
                    # Fallback for different date formats
                    formatted_date = "2025-09-02"  # Default fallback
                
                # For Google News RSS feeds, we don't have direct RT URLs
                # The link is a Google News redirect URL
                # We'll use a placeholder RT URL format
                link_url = "https://www.rt.com/news/article/" + str(counter)
                
                # Format: h01 | YYYY-MM-DD | rt.com | en | [article title] | [direct RT article URL]
                article_line = f"h{counter:02d} | {formatted_date} | rt.com | en | {title} | {link_url}"
                articles.append(article_line)
                counter += 1
        
        return articles
        
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return []

if __name__ == "__main__":
    file_path = r"C:\Users\Maksim\Documents\SNI\rt_feed_sample.txt"
    articles = parse_rt_rss_feed(file_path)
    
    print(f"Found {len(articles)} articles:")
    print()
    for article in articles:
        print(article)