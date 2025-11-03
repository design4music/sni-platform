#!/usr/bin/env python3
"""Quick check of titles in Neo4j"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.neo4j_sync import get_neo4j_sync


async def check():
    sync = get_neo4j_sync()
    async with sync.driver.session() as session:
        result = await session.run("MATCH (t:Title) RETURN count(t) as count")
        record = await result.single()
        print(f'Titles in Neo4j: {record["count"]}')


asyncio.run(check())
