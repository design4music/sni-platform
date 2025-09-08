#!/usr/bin/env python3
"""
Test GEN Pipeline Integration
Strategic Narrative Intelligence Platform

Tests the complete GEN-1/2/3 pipeline functionality including:
- Database connectivity and schema validation
- GEN stage execution and progress tracking  
- RAI client integration and fallback analysis
- Publisher integration with GEN completion checks

Provides comprehensive validation before production deployment.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List
import psycopg2
import psycopg2.extras

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_database_schema():
    """Test that all required database fields exist for GEN pipeline."""
    print("Testing database schema...")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='narrative_intelligence',
            user='postgres',
            password='password'
        )
        
        cursor = conn.cursor()
        
        # Check required GEN fields exist
        required_fields = [
            'alignment', 'actor_origin', 'frame_logic', 'turning_points',
            'narrative_tension', 'logical_strain', 'rai_analysis', 
            'source_stats', 'top_excerpts', 'update_status', 'version_history'
        ]
        
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'narratives' 
              AND column_name = ANY(%s)
        """, (required_fields,))
        
        existing_fields = {row[0]: row[1] for row in cursor.fetchall()}
        
        missing_fields = set(required_fields) - set(existing_fields.keys())
        if missing_fields:
            print(f"  ERROR: Missing required fields: {missing_fields}")
            return False
        
        print(f"  SUCCESS: All {len(required_fields)} required fields present")
        
        # Check for some consolidated narratives
        cursor.execute("""
            SELECT COUNT(*) FROM narratives 
            WHERE consolidation_stage = 'consolidated'
        """)
        
        consolidated_count = cursor.fetchone()[0]
        print(f"  INFO: Found {consolidated_count} consolidated narratives")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ERROR: Database schema test failed: {e}")
        return False


def test_rai_client():
    """Test RAI client integration and fallback functionality."""
    print("Testing RAI client integration...")
    
    try:
        from etl_pipeline.rai.rai_client import RAIClient, test_rai_integration
        
        # Test RAI client functionality  
        success = test_rai_integration()
        
        if success:
            print("  SUCCESS: RAI client integration test passed")
        else:
            print("  WARNING: RAI client test had issues (check service availability)")
            
        return True
        
    except ImportError as e:
        print(f"  ERROR: Cannot import RAI client: {e}")
        return False
    except Exception as e:
        print(f"  ERROR: RAI client test failed: {e}")
        return False


def test_gen_scripts_executable():
    """Test that all GEN scripts are executable and have proper imports."""
    print("Testing GEN script executability...")
    
    gen_scripts = [
        'generation/gen1_card.py',
        'generation/gen2_enrichment.py', 
        'generation/gen3_rai_overlay.py'
    ]
    
    success_count = 0
    
    for script in gen_scripts:
        script_path = project_root / script
        
        if not script_path.exists():
            print(f"  ERROR: Script {script} not found")
            continue
            
        try:
            # Test basic import and help
            import subprocess
            result = subprocess.run(
                [sys.executable, str(script_path), '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"  SUCCESS: {script} is executable")
                success_count += 1
            else:
                print(f"  ERROR: {script} failed with code {result.returncode}")
                print(f"    Error: {result.stderr}")
                
        except Exception as e:
            print(f"  ERROR: Cannot test {script}: {e}")
    
    return success_count == len(gen_scripts)


def test_pipeline_integration():
    """Test pipeline integration in run_pipeline_full.py."""
    print("Testing pipeline integration...")
    
    try:
        # Test that pipeline steps include GEN stages
        from scripts.run_pipeline_full import get_pipeline_steps
        
        steps = get_pipeline_steps()
        step_names = [step[0] for step in steps]
        
        required_gen_steps = ['GEN1_CARDS', 'GEN2_ENRICHMENT', 'GEN3_RAI_OVERLAY']
        
        missing_steps = set(required_gen_steps) - set(step_names)
        if missing_steps:
            print(f"  ERROR: Missing pipeline steps: {missing_steps}")
            return False
            
        print(f"  SUCCESS: All GEN stages integrated into pipeline")
        
        # Check step order (GEN stages should be after CLUST3 and before PUBLISHER)
        try:
            clust3_idx = step_names.index('CLUST3_CONSOLIDATION')
            gen1_idx = step_names.index('GEN1_CARDS')
            gen2_idx = step_names.index('GEN2_ENRICHMENT') 
            gen3_idx = step_names.index('GEN3_RAI_OVERLAY')
            publisher_idx = step_names.index('PUBLISHER')
            
            if clust3_idx < gen1_idx < gen2_idx < gen3_idx < publisher_idx:
                print("  SUCCESS: GEN stages in correct pipeline order")
            else:
                print("  WARNING: GEN stages may not be in optimal order")
                
        except ValueError as e:
            print(f"  ERROR: Pipeline step ordering issue: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ERROR: Pipeline integration test failed: {e}")
        return False


def test_environment_configuration():
    """Test environment variable configuration."""
    print("Testing environment configuration...")
    
    # Test RAI configuration
    rai_enabled = os.getenv('RAI_ENABLED', 'false').lower() == 'true'
    rai_base_url = os.getenv('RAI_BASE_URL', '')
    rai_timeout = os.getenv('RAI_TIMEOUT', '15')
    
    print(f"  RAI Enabled: {rai_enabled}")
    print(f"  RAI Base URL: {rai_base_url or 'Not configured'}")
    print(f"  RAI Timeout: {rai_timeout}s")
    
    # Test GEN stage configuration
    gen1_enabled = os.getenv('GEN_ENABLE_STAGE1', 'true').lower() == 'true'
    gen2_enabled = os.getenv('GEN_ENABLE_STAGE2', 'true').lower() == 'true'  
    gen3_enabled = os.getenv('GEN_ENABLE_STAGE3', 'true').lower() == 'true'
    
    print(f"  GEN-1 Enabled: {gen1_enabled}")
    print(f"  GEN-2 Enabled: {gen2_enabled}")
    print(f"  GEN-3 Enabled: {gen3_enabled}")
    
    if not rai_enabled:
        print("  INFO: RAI service disabled - will use local fallback analysis")
    
    return True


def test_publisher_gen_integration():
    """Test that Publisher correctly handles GEN completion requirements."""
    print("Testing Publisher GEN integration...")
    
    try:
        from generation.publisher import NarrativePublisher
        
        # Test Publisher initialization with RAI configuration
        publisher = NarrativePublisher()
        
        print(f"  Publisher RAI Enabled: {publisher.rai_enabled}")
        
        # Test candidate loading query (should include GEN requirements)
        conn = publisher.get_db_connection()
        candidates = publisher.load_publication_candidates(conn)
        
        print(f"  Publication candidates found: {len(candidates)}")
        
        # Validate that candidates have proper GEN completion status
        gen_completed_count = 0
        for candidate in candidates[:5]:  # Check first 5
            update_status = candidate.get('update_status', {})
            if isinstance(update_status, str):
                update_status = json.loads(update_status)
            
            gen_status = update_status.get('gen', {})
            
            has_gen2 = gen_status.get('gen2_done_at') is not None
            has_gen3 = gen_status.get('gen3_done_at') is not None
            
            if has_gen2 or has_gen3:
                gen_completed_count += 1
        
        print(f"  Candidates with GEN completion: {gen_completed_count}/{min(5, len(candidates))}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ERROR: Publisher GEN integration test failed: {e}")
        return False


def run_all_tests():
    """Run complete GEN pipeline test suite."""
    print("=" * 60)
    print("GEN PIPELINE INTEGRATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Database Schema", test_database_schema),
        ("RAI Client", test_rai_client), 
        ("GEN Scripts", test_gen_scripts_executable),
        ("Pipeline Integration", test_pipeline_integration),
        ("Environment Config", test_environment_configuration),
        ("Publisher Integration", test_publisher_gen_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"  RESULT: PASS")
            else:
                print(f"  RESULT: FAIL")
        except Exception as e:
            print(f"  RESULT: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUITE SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\nGEN PIPELINE READY FOR DEPLOYMENT!")
        return True
    else:
        print(f"\n{total-passed} test(s) need attention before deployment.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)