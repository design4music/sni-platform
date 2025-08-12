#!/usr/bin/env python3
"""
Convert GDELT themes Excel file to JSON format for taxonomy loading.
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def convert_gdelt_excel_to_json(excel_file, output_file):
    """Convert GDELT Excel file to JSON format."""
    logger.info(f"Converting GDELT Excel file: {excel_file}")
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_file)
        logger.info(f"Loaded Excel with {len(df)} rows and columns: {list(df.columns)}")
        
        # Inspect the data structure
        logger.info("First 5 rows:")
        for i in range(min(5, len(df))):
            logger.info(f"  Row {i}: {dict(df.iloc[i])}")
        
        topics = []
        aliases = []
        
        # Try to identify the theme column
        theme_column = None
        for col in df.columns:
            col_lower = col.lower()
            if 'theme' in col_lower or 'category' in col_lower or 'name' in col_lower:
                theme_column = col
                break
        
        if not theme_column and len(df.columns) > 0:
            # Use first column if no clear theme column found
            theme_column = df.columns[0]
        
        if not theme_column:
            logger.error("Could not identify theme column")
            return
        
        logger.info(f"Using column '{theme_column}' as theme names")
        
        # Process each theme
        for idx, row in df.iterrows():
            theme_name = row[theme_column]
            
            # Skip empty rows
            if pd.isna(theme_name) or not str(theme_name).strip():
                continue
            
            theme_name = str(theme_name).strip()
            
            # Create topic ID from name (clean and uppercase)
            topic_id_clean = theme_name.upper().replace(' ', '_').replace('/', '_')
            topic_id_clean = ''.join(c for c in topic_id_clean if c.isalnum() or c == '_')
            
            topic_entry = {
                "topic_id": f"gdelt:{topic_id_clean}",
                "name": theme_name,
                "source": "GDELT", 
                "parent_id": None,
                "path": []
            }
            topics.append(topic_entry)
            
            # Create alias
            aliases.append({
                "topic_id": f"gdelt:{topic_id_clean}",
                "alias": theme_name,
                "lang": "en"
            })
        
        # Create output structure
        output_data = {
            "topics": topics,
            "aliases": aliases
        }
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully converted {len(topics)} GDELT themes to {output_file}")
        logger.info("Sample themes:")
        for topic in topics[:10]:
            logger.info(f"  - {topic['topic_id']}: {topic['name']}")
        
        return len(topics)
        
    except Exception as e:
        logger.error(f"Failed to convert GDELT Excel: {e}")
        return None


def main():
    """Main conversion function."""
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    
    excel_file = data_dir / "gdelt_themes.xlsx"
    json_file = data_dir / "gdelt_themes.json"
    
    if not excel_file.exists():
        logger.error(f"Excel file not found: {excel_file}")
        sys.exit(1)
    
    # Convert Excel to JSON
    theme_count = convert_gdelt_excel_to_json(excel_file, json_file)
    
    if theme_count:
        logger.info(f"SUCCESS: Converted {theme_count} GDELT themes")
        print(f"Output file: {json_file}")
        print(f"Next step: Run sync_taxonomies.py to load into database")
    else:
        logger.error("Failed to convert GDELT themes")
        sys.exit(1)


if __name__ == "__main__":
    main()