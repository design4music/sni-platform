#!/usr/bin/env python3
"""
Sequential Batcher - Simple Performance-Optimized Batching
NO entity extraction, NO complex logic - just chunk titles into batches by size.
"""

from typing import Any, Dict, List


def group_titles_sequentially(
    titles: List[Dict[str, Any]], batch_size: int = 100
) -> List[Dict[str, Any]]:
    """
    Group titles into sequential batches for optimal LLM processing.

    This is the SIMPLEST possible batching - no entity extraction, no complex logic.
    Just divide titles into equal-sized chunks for maximum LLM efficiency.

    Args:
        titles: List of title dictionaries
        batch_size: Number of titles per batch (default: 100 for optimal LLM performance)

    Returns:
        List of batch dictionaries with 'titles', 'batch_key', and 'size'
    """
    if not titles:
        return []

    batches = []

    for i in range(0, len(titles), batch_size):
        batch_titles = titles[i : i + batch_size]
        batch_number = (i // batch_size) + 1

        batch_info = {
            "titles": batch_titles,
            "batch_key": f"sequential_batch_{batch_number}",
            "size": len(batch_titles),
            "start_index": i,
            "end_index": i + len(batch_titles) - 1,
        }

        batches.append(batch_info)

    return batches


def extract_batch_context(batch_titles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract simple context from a batch of titles (no complex entity analysis).

    Args:
        batch_titles: List of title dictionaries

    Returns:
        Simple batch context dictionary
    """
    if not batch_titles:
        return {}

    # Simple statistics
    total_titles = len(batch_titles)
    sources = set(title.get("source", "Unknown") for title in batch_titles)

    # Date range
    dates = [
        title.get("pubdate_utc") for title in batch_titles if title.get("pubdate_utc")
    ]
    earliest_date = min(dates) if dates else None
    latest_date = max(dates) if dates else None

    return {
        "total_titles": total_titles,
        "unique_sources": len(sources),
        "source_list": sorted(list(sources)),
        "earliest_date": earliest_date,
        "latest_date": latest_date,
        "date_span_hours": (
            (latest_date - earliest_date).total_seconds() / 3600
            if earliest_date and latest_date
            else 0
        ),
    }


if __name__ == "__main__":
    # Test with sample data
    sample_titles = [
        {"id": f"title_{i}", "text": f"Sample title {i}", "source": "Source A"}
        for i in range(250)
    ]

    print("Testing sequential batching:")

    # Test different batch sizes
    for batch_size in [50, 100, 150]:
        batches = group_titles_sequentially(sample_titles, batch_size=batch_size)
        print(f"\nBatch size {batch_size}: {len(batches)} batches")
        for i, batch in enumerate(batches):
            print(f"  Batch {i+1}: {batch['size']} titles ({batch['batch_key']})")
