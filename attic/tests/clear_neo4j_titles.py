import asyncio

from core.neo4j_sync import get_neo4j_sync


async def clear():
    neo = get_neo4j_sync()
    async with neo.driver.session() as sess:
        await sess.run("MATCH (t:Title) DETACH DELETE t")
    print("Titles cleared from Neo4j")


asyncio.run(clear())
