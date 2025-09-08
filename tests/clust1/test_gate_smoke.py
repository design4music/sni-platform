"""
CLUST-001 Strategic Gate Smoke Tests
Validates actor matching and edge cases across languages
"""

import pytest

from apps.clust1.strategic_gate import StrategicGate, filter_titles_batch
from apps.clust1.vocab_loader import validate_vocabularies


class TestStrategicGateSmoke:
    """Smoke tests for Strategic Gate filtering"""

    @pytest.fixture(scope="class")
    def gate(self):
        """Initialize Strategic Gate once per test class"""
        return StrategicGate()

    def test_vocabulary_files_exist(self):
        """Validate that vocabulary files are present and well-formed"""
        validation = validate_vocabularies()

        assert validation["actors_file_exists"], "actors.csv file missing"
        assert validation["actors_count"] > 0, "No actors loaded"
        assert (
            len(validation["errors"]) == 0
        ), f"Vocabulary errors: {validation['errors']}"

        print(f"[PASS] Loaded {validation['actors_count']} actors")

    def test_actor_hit_eu_sanctions(self, gate):
        """Test actor hit - EU sanctions (hits EU actor)"""
        result = gate.filter_title(
            "EU imposes sanctions on Iranian officials over human rights"
        )

        assert result.keep is True
        assert result.reason == "actor_hit"
        assert result.score == 0.99
        assert result.actor_hit in ["EU", "IR"]  # Should hit EU or Iran actor

        print(f"[PASS] EU/Iran actor hit: actor={result.actor_hit}")

    def test_actor_hit_beijing(self, gate):
        """Test actor alias match - Beijing warns"""
        result = gate.filter_title("Beijing warns against Taiwan independence moves")

        assert result.keep is True
        assert result.reason == "actor_hit"
        assert result.score == 0.99
        assert result.actor_hit in ["CN", "China"]  # Could be mapped to either

        print(f"[PASS] Beijing actor hit: actor={result.actor_hit}")

    def test_actor_hit_spain_madrid(self, gate):
        """Test actor hit - Madrid/Spain actor match"""
        result = gate.filter_title("Barcelona defeats Real Madrid 3-1 in El Clasico")

        assert result.keep is True
        assert result.reason == "actor_hit"  # Madrid matches Spain actor
        assert result.score == 0.99
        assert result.actor_hit == "ES"  # Spain actor

        print(f"[PASS] Spain/Madrid actor hit: actor={result.actor_hit}")

    def test_no_actor_pure_sports(self, gate):
        """Test no actor case - pure sports with no geopolitical mentions"""
        result = gate.filter_title("Team Alpha defeats Team Beta in championship match")

        assert result.keep is False
        assert result.reason == "no_actor"
        assert result.score == 0.0

        print(f"[PASS] Sports no actor: score={result.score}")

    def test_multilingual_russian(self, gate):
        """Test Russian text processing"""
        result = gate.filter_title("Россия объявляет новые санкции против ЕС")

        # Should hit actor (Russia)
        assert result.keep is True
        assert result.reason == "actor_hit"

        print(f"[PASS] Russian text: reason={result.reason}, actor={result.actor_hit}")

    def test_multilingual_chinese(self, gate):
        """Test Chinese text processing"""
        result = gate.filter_title("中国警告美国不要干预台湾问题")

        # Should hit actor (China/中国)
        assert result.keep is True
        assert result.reason == "actor_hit"
        # Chinese aliases use substring matching, not word boundaries

        print(f"[PASS] Chinese text: reason={result.reason}, actor={result.actor_hit}")

    def test_no_strategic_content(self, gate):
        """Test non-strategic content without actors"""
        result = gate.filter_title("Local restaurant opens new location downtown")

        # Should not hit any actors
        assert result.keep is False
        assert result.reason == "no_actor"
        assert result.score == 0.0

        print(f"[PASS] Non-strategic content: reason={result.reason}")

    def test_edge_case_empty_text(self, gate):
        """Test empty/whitespace text handling"""
        result = gate.filter_title("")
        assert result.keep is False
        assert result.score == 0.0

        result = gate.filter_title("   \t\n   ")
        assert result.keep is False
        assert result.score == 0.0

        print("[PASS] Empty text handled correctly")

    def test_batch_processing(self, gate):
        """Test batch filtering optimization"""
        test_titles = [
            {"title_norm": "EU imposes sanctions on Iranian officials"},
            {"title_norm": "Beijing warns against Taiwan independence"},
            {"title_norm": "Team Alpha defeats Team Beta in championship match"},
            {"title_norm": "Russia announces new export controls"},
            {"title_norm": ""},
        ]

        results = filter_titles_batch(test_titles)
        assert len(results) == 5

        # Check specific results
        eu_title, eu_result = results[0]
        assert eu_result.keep is True
        assert eu_result.reason == "actor_hit"  # EU or Iran actor hit

        beijing_title, beijing_result = results[1]
        assert beijing_result.keep is True
        assert beijing_result.reason == "actor_hit"

        sports_title, sports_result = results[2]
        assert sports_result.keep is False
        assert sports_result.reason == "no_actor"

        russia_title, russia_result = results[3]
        assert russia_result.keep is True
        assert russia_result.reason == "actor_hit"  # Russia actor

        empty_title, empty_result = results[4]
        assert empty_result.keep is False

        print("[PASS] Batch processing works correctly")

    def test_actor_boundary_precision(self, gate):
        """Test word boundary fixes for false positives"""
        # Test cases that should NOT match
        false_positives = [
            ("Visit the museum today", "EU"),  # "mus-EU-m" should not match EU
            ("New temu shopping app", "EU"),  # "t-EU" should not match EU
            ("Brokeback Mountain story", "KR"),  # "b-ROK-eback" should not match KR/ROK
        ]

        for title, should_not_match in false_positives:
            result = gate.filter_title(title)
            if result.keep:
                assert (
                    result.actor_hit != should_not_match
                ), f"False positive: '{title}' matched {should_not_match}"

        # Test cases that SHOULD match
        true_positives = [
            ("EU leaders meet today", "EU"),
            ("ROK announces new policy", "KR"),  # ROK maps to KR
        ]

        for title, should_match in true_positives:
            result = gate.filter_title(title)
            assert result.keep is True, f"Should match: '{title}'"
            assert result.reason == "actor_hit"

        print("[PASS] Word boundary precision working")


if __name__ == "__main__":
    # Quick smoke test when run directly
    print("CLUST-001 Strategic Gate Smoke Test")
    print("=" * 50)

    try:
        gate = StrategicGate()
        test_instance = TestStrategicGateSmoke()

        # Run key tests
        test_instance.test_vocabulary_files_exist()
        test_instance.test_actor_hit_eu_sanctions(gate)
        test_instance.test_actor_hit_beijing(gate)
        test_instance.test_no_actor_pure_sports(gate)
        test_instance.test_multilingual_russian(gate)
        test_instance.test_multilingual_chinese(gate)
        test_instance.test_edge_case_empty_text(gate)
        test_instance.test_batch_processing(gate)
        test_instance.test_actor_boundary_precision(gate)

        print("\n" + "=" * 50)
        print("[PASS] ALL SMOKE TESTS PASSED")
        print("Strategic Gate is ready for production use!")

    except Exception as e:
        print(f"\n[FAIL] SMOKE TEST FAILED: {e}")
        raise
