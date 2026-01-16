"""
Full Pipeline Test Runner
Runs Phase 1-2-3 + Taxonomy Tools with timing and reporting
"""
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

# Output report file
REPORT_FILE = Path(__file__).parent / "pipeline_test_report.json"

def run_phase(phase_name, command, cwd=None):
    """Run a phase and capture timing + output"""
    print("=" * 60)
    print(f"STARTING: {phase_name}")
    print("=" * 60)

    start_time = time.time()
    start_datetime = datetime.now()

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per phase
        )

        end_time = time.time()
        duration = end_time - start_time

        success = result.returncode == 0

        # Extract key stats from output
        output_lines = result.stdout.split('\n')

        phase_result = {
            "phase": phase_name,
            "start_time": start_datetime.isoformat(),
            "duration_seconds": round(duration, 2),
            "duration_formatted": f"{int(duration // 60)}m {int(duration % 60)}s",
            "success": success,
            "exit_code": result.returncode,
            "output_lines": len(output_lines),
            "stdout": result.stdout,
            "stderr": result.stderr
        }

        # Try to extract statistics from output
        stats = extract_stats(output_lines, phase_name)
        if stats:
            phase_result["statistics"] = stats

        # Print summary
        status = "SUCCESS" if success else "FAILED"
        print(f"\n{status}: {phase_name}")
        print(f"Duration: {phase_result['duration_formatted']}")
        if stats:
            print("Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

        return phase_result

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"\nTIMEOUT: {phase_name} exceeded 10 minutes")
        return {
            "phase": phase_name,
            "start_time": start_datetime.isoformat(),
            "duration_seconds": round(duration, 2),
            "success": False,
            "error": "Timeout after 10 minutes"
        }
    except Exception as e:
        duration = time.time() - start_time
        print(f"\nERROR: {phase_name} - {e}")
        return {
            "phase": phase_name,
            "start_time": start_datetime.isoformat(),
            "duration_seconds": round(duration, 2),
            "success": False,
            "error": str(e)
        }

def extract_stats(output_lines, phase_name):
    """Extract statistics from phase output"""
    stats = {}

    for line in output_lines:
        line = line.strip()

        # Phase 1 stats
        if "Total feeds processed:" in line:
            stats["feeds_processed"] = line.split(":")[-1].strip()
        if "Total titles fetched:" in line:
            stats["titles_fetched"] = line.split(":")[-1].strip()
        if "New titles inserted:" in line:
            stats["new_titles"] = line.split(":")[-1].strip()
        if "Duplicates skipped:" in line:
            stats["duplicates"] = line.split(":")[-1].strip()

        # Phase 2 stats
        if "Total processed:" in line and "Phase 2" in phase_name:
            stats["total_processed"] = line.split(":")[-1].strip()
        if "Matched:" in line:
            stats["matched"] = line.split(":")[-1].strip()
        if "Multi-centroid:" in line:
            stats["multi_centroid"] = line.split(":")[-1].strip()
        if "Blocked (stop words):" in line:
            stats["blocked_stopwords"] = line.split(":")[-1].strip()
        if "No match (out of scope):" in line:
            stats["out_of_scope"] = line.split(":")[-1].strip()

        # Phase 3 stats
        if "Total processed:" in line and "Phase 3" in phase_name:
            stats["total_processed"] = line.split(":")[-1].strip()
        if "Successfully assigned:" in line:
            stats["assigned"] = line.split(":")[-1].strip()
        if "Errors:" in line and "Phase 3" in phase_name:
            stats["errors"] = line.split(":")[-1].strip()

        # Taxonomy tools stats
        if "Found" in line and "candidates" in line:
            parts = line.split()
            if len(parts) >= 2:
                stats["candidates_found"] = parts[1]

    return stats if stats else None

def main():
    print("\n" + "=" * 60)
    print("FULL PIPELINE TEST - 133 ACTIVE FEEDS")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    overall_start = time.time()

    results = []

    # Phase 1: RSS Ingestion (no max-feeds limit - process all 133)
    phase1 = run_phase(
        "Phase 1: RSS Ingestion",
        ["python", "-m", "v3.phase_1.ingest_feeds"]
    )
    results.append(phase1)

    if not phase1["success"]:
        print("\nPhase 1 failed. Stopping pipeline.")
        save_report(results, overall_start)
        return

    # Phase 2: Centroid Matching (no max-titles limit - process all pending)
    phase2 = run_phase(
        "Phase 2: Centroid Matching",
        ["python", "-m", "v3.phase_2.match_centroids"]
    )
    results.append(phase2)

    if not phase2["success"]:
        print("\nPhase 2 failed. Stopping pipeline.")
        save_report(results, overall_start)
        return

    # Phase 3: Track Assignment (no max-ctms limit - process all assigned)
    phase3 = run_phase(
        "Phase 3: Track Assignment",
        ["python", "-m", "v3.phase_3.assign_tracks"]
    )
    results.append(phase3)

    # Taxonomy Tools (continue even if Phase 3 has errors)

    # NameBombs
    namebombs = run_phase(
        "Taxonomy: NameBombs Detector",
        ["python", "-m", "v3.taxonomy_tools.namebombs", "--since-hours", "24"]
    )
    results.append(namebombs)

    # OOS Keyword Candidates
    oos_keywords = run_phase(
        "Taxonomy: OOS Keyword Candidates",
        ["python", "-m", "v3.taxonomy_tools.oos_keyword_candidates", "--since-hours", "24"]
    )
    results.append(oos_keywords)

    # Generate final report
    save_report(results, overall_start)

    print("\n" + "=" * 60)
    print("PIPELINE TEST COMPLETE")
    print("=" * 60)
    print(f"Report saved to: {REPORT_FILE}")

def save_report(results, overall_start):
    """Save detailed report to JSON file"""
    overall_duration = time.time() - overall_start

    report = {
        "test_run": {
            "timestamp": datetime.now().isoformat(),
            "total_duration_seconds": round(overall_duration, 2),
            "total_duration_formatted": f"{int(overall_duration // 60)}m {int(overall_duration % 60)}s",
            "phases_completed": len(results),
            "all_successful": all(r.get("success", False) for r in results)
        },
        "phases": results
    }

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary table
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Phase':<40} | {'Duration':<10} | {'Status':<10}")
    print("-" * 60)

    for result in results:
        phase = result['phase']
        duration = result.get('duration_formatted', 'N/A')
        status = 'SUCCESS' if result.get('success') else 'FAILED'
        print(f"{phase:<40} | {duration:<10} | {status:<10}")

    print("-" * 60)
    total_duration = f"{int(overall_duration // 60)}m {int(overall_duration % 60)}s"
    print(f"{'TOTAL':<40} | {total_duration:<10} |")
    print("=" * 60)

if __name__ == "__main__":
    main()
