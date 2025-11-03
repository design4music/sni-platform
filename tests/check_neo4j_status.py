import asyncio

from core.neo4j_sync import get_neo4j_sync


async def check():
    neo = get_neo4j_sync()
    async with neo.driver.session() as sess:
        title_count = await sess.run("MATCH (t:Title) RETURN count(t) as count")
        title_result = await title_count.single()

        entity_count = await sess.run("MATCH (e:Entity) RETURN count(e) as count")
        entity_result = await entity_count.single()

        print(f"Neo4j status:")
        print(f'  Title nodes: {title_result["count"]}')
        print(f'  Entity nodes: {entity_result["count"]}')


asyncio.run(check())
