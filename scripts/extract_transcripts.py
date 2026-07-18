"""Extract markdown content from agent transcript files and write to output files."""

import json
import os
import sys

TASKS_DIR = os.path.join(
    os.environ["LOCALAPPDATA"],
    "Temp",
    "claude",
    "C--Users-Maksim-Documents-SNI",
    "tasks",
)
OUT_DIR = r"C:\Users\Maksim\Documents\SNI\out"

# (transcript_id, [list of output filenames])
MAPPINGS = [
    ("aee7fba244a083ea7", ["analysis_1_content_richness.md"]),
    ("a6d20a3506ba330a4", ["analysis_2_signal_network.md"]),
    ("a3118ffe8930ed247", ["analysis_3_event_scale.md", "analysis_4_temporal.md"]),
    ("ae3266aca01515b3b", ["analysis_5_track_balance.md", "analysis_6_bilateral.md"]),
    ("a6f180d6f8501c744", ["analysis_7_publishers.md"]),
]


def extract_write_contents(filepath):
    """Read JSONL file, find Write tool_use entries, return list of content strings."""
    contents = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Navigate: message.content[] -> tool_use with name Write
            msg = obj.get("message", {})
            content_list = msg.get("content", [])
            if not isinstance(content_list, list):
                continue
            for block in content_list:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_use"
                    and block.get("name") == "Write"
                ):
                    inp = block.get("input", {})
                    md_content = inp.get("content", "")
                    if md_content:
                        contents.append(md_content)
    return contents


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    errors = 0

    for transcript_id, output_names in MAPPINGS:
        src = os.path.join(TASKS_DIR, transcript_id + ".output")
        if not os.path.isfile(src):
            print("ERROR: transcript not found: %s" % src)
            errors += 1
            continue

        contents = extract_write_contents(src)
        expected = len(output_names)
        if len(contents) != expected:
            print(
                "WARNING: %s -- expected %d Write calls, found %d"
                % (transcript_id, expected, len(contents))
            )

        for i, out_name in enumerate(output_names):
            out_path = os.path.join(OUT_DIR, out_name)
            if i < len(contents):
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(contents[i])
                print("OK: wrote %s" % out_path)
            else:
                print("ERROR: no content for %s" % out_name)
                errors += 1

    # Verify
    print("\n--- Verification ---")
    for _, output_names in MAPPINGS:
        for name in output_names:
            path = os.path.join(OUT_DIR, name)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                print("  %s: %d lines" % (name, len(lines)))
            else:
                print("  %s: MISSING" % name)

    sys.exit(errors)


if __name__ == "__main__":
    main()
