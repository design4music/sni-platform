"""Check and fix alias format for 18 specific items"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def check_and_fix_18_items():
    """Check and fix alias format for specified items"""

    item_ids = [
        "b2858a2d-b875-4377-8019-1470b3e017c3",
        "ec415b00-bece-44b8-a2d3-7ef9dd2a2331",
        "254c0b1a-c087-4343-b88f-484a929396f6",
        "91c8ced0-e457-4642-a574-5fdda7077f63",
        "af1aef95-7531-49f2-af92-dae2e29ce667",
        "0f343004-2c0f-4693-9c3f-62a8b254b265",
        "d472e10b-a5cf-4fe5-b295-f7c14c6b69c9",
        "f30d9c34-b1e4-4f95-96e5-1d18c5eb3810",
        "015fc889-54e6-4549-8bed-2ddd4392f232",
        "1a3f6a30-895a-47e6-a1ba-050146f742c0",
        "a926242a-3b4a-4708-8999-d683bcb62de2",
        "5e405f5f-54bf-487d-8763-9b39f222817c",
        "45b523b8-5257-4521-aa9b-d11b33d22176",
        "14264c6d-37f4-4b35-a20d-1af1d570697c",
        "eb642b35-eedc-42e8-bcaa-7b346a327e67",
        "1502fd75-2c13-47da-8d4d-f4b14bedcfca",
        "68ec3175-5be7-4ce3-abb8-51c2c3c366bc",
        "dbfe9295-262c-47ed-9160-0dee2ec6e7b5",
    ]

    try:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )
        conn.autocommit = False

        with conn.cursor() as cur:
            print("Checking 18 items for alias format...\n")

            items_to_fix = []

            for item_id in item_ids:
                cur.execute(
                    """
                    SELECT id, item_raw, item_type, aliases
                    FROM taxonomy_v3
                    WHERE id = %s
                """,
                    (item_id,),
                )
                result = cur.fetchone()

                if result:
                    id, item_raw, item_type, aliases = result

                    # Check if aliases is a flat array (needs fixing)
                    if isinstance(aliases, list):
                        print(f"[NEEDS FIX] {item_raw:30} (ID: {id})")
                        print(
                            f"            Current format: flat array with {len(aliases)} aliases"
                        )
                        items_to_fix.append(
                            {"id": id, "item_raw": item_raw, "aliases": aliases}
                        )
                    elif isinstance(aliases, dict):
                        # Check if it's language-code format
                        if any(key in aliases for key in ["ar", "en", "de"]):
                            print(
                                f"[OK]        {item_raw:30} (already language-code format)"
                            )
                        else:
                            print(
                                f"[UNKNOWN]   {item_raw:30} (dict but not language-code)"
                            )
                    else:
                        print(f"[ERROR]     {item_raw:30} (unexpected format)")
                else:
                    print(f"[NOT FOUND] ID: {item_id}")

            if items_to_fix:
                print(f"\n{'='*60}")
                print(f"Found {len(items_to_fix)} items needing conversion")
                print(f"{'='*60}\n")
                print("Please provide the proper language-code format for these items:")
                for item in items_to_fix:
                    print(f"\nItem: {item['item_raw']}")
                    print(f"Current aliases: {item['aliases']}")
            else:
                print("\nAll items are already in correct format!")

        conn.close()
        return True

    except Exception as e:
        print(f"Check failed: {e}")
        if conn:
            conn.close()
        return False


if __name__ == "__main__":
    success = check_and_fix_18_items()
    sys.exit(0 if success else 1)
