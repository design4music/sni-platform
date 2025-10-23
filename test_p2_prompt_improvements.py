#!/usr/bin/env python3
"""
Test Phase 2 Prompt Improvements
Tests the enhanced strategic review prompt against problematic titles from titles.txt
"""

import asyncio

from core.llm_client import LLMClient

# Test cases from docs/tickets/titles.txt
TEST_TITLES = {
    # Group 1: Non-strategic wrongly classified (should be strategic=0)
    "non_strategic": [
        "Train cancellations in Cologne and Hamburg: Cable damage and defective signal box",
        "ACGN fans fuel national day's tourism vigor",
        "Motivation and involvement: the new levers to boost productivity",
        "Milton Leite files criminal complaint and accuses Jockey's lawyers of racism",
        "Informal traders evicted from Joburg thrift haven as city launches crackdown",
        "Olympic boost offers squash springboard for bright future",
        "First Brands creditor claims as much as $2.3bn has 'simply vanished'",
        "Ex-FCTA director jailed 24 years for N318m fraud case",
        "Bus crash in South African mountains kills at least 42",
        "3 employees of the Qatari Amiri Diwan died in a traffic accident in Sharm el-Sheikh",
        "A day after he revealed his 'betrayal.' Fire breaks out at Vinicius' house",
        "Furstenzell: Walker discovers human remains in the forest",
        "Police shoot at man with gun in Dusseldorf center",
        "Shanghai index hits 10-year high on policy momentum",
        "Kishore, Edwin emerge champions at Horwitz Bishop Rapid Chess Tournament",
        "BR employee takes over 170,000 CDs: 'Couldn't stand by and watch it being destroyed'",
        "Man kills young businesswoman, attempts suicide in Milan",
    ],
    # Group 2: Strategic with location inference (should extract entities)
    "strategic_with_location": [
        (
            "News outlets broadly reject Pentagon rules before deadline for signing",
            ["Pentagon", "United States"],
        ),
        (
            "The Justice asked the Chamber of Deputies for authorization to move forward with measures against Espert",
            ["Argentina"],
        ),
        ("The AI valuation bubble is now getting silly | Nils Pratley", ["AI"]),
        (
            "Witnesses who could shed light on the cause of deadly Tennessee blast were killed",
            ["Tennessee", "United States"],
        ),
        (
            "Delhi 2020 riots: police 'singled me out', Umar Khalid tells court",
            ["Delhi", "India"],
        ),
        (
            "30th Macao int'l trade, investment fair to highlight innovation",
            ["Macao", "China"],
        ),
        (
            "16 people died in a blast at a Tennessee explosives factory early Friday, the sheriff says",
            ["Tennessee", "United States"],
        ),
    ],
    # Group 4: Incoherent/meaningless titles (should be strategic=0)
    "incoherent": [
        "Shutdown Politics, Air Traffic Control Issues, Comey Arraignment",
        "Army rescues 37 hostages, kills 9 terrorists in anti-crime operations",
    ],
}


async def test_prompt_improvements():
    """Test the enhanced Phase 2 prompt against problematic titles"""
    print("=" * 80)
    print("PHASE 2 PROMPT IMPROVEMENTS TEST")
    print("=" * 80)

    llm_client = LLMClient()

    # Test Group 1: Non-strategic titles (should all be strategic=0)
    print("\n" + "=" * 80)
    print("GROUP 1: Non-Strategic Titles (should be filtered OUT)")
    print("=" * 80)

    non_strategic_results = []
    for title in TEST_TITLES["non_strategic"]:
        result = await llm_client.strategic_review(title)
        non_strategic_results.append(result)

        status = "✓ PASS" if not result["is_strategic"] else "✗ FAIL"
        print(f"\n{status}")
        print(f"Title: {title[:80]}")
        print(f"Strategic: {result['is_strategic']}")
        print(f"Entities: {result.get('entities', [])}")

    # Calculate accuracy for Group 1
    correct_non_strategic = sum(
        1 for r in non_strategic_results if not r["is_strategic"]
    )
    accuracy_group1 = (correct_non_strategic / len(non_strategic_results)) * 100
    print(f"\n{'='*80}")
    print(
        f"GROUP 1 ACCURACY: {correct_non_strategic}/{len(non_strategic_results)} = {accuracy_group1:.1f}%"
    )

    # Test Group 2: Strategic with location inference (should be strategic=1 with entities)
    print("\n" + "=" * 80)
    print("GROUP 2: Strategic Titles with Location Hints (should extract entities)")
    print("=" * 80)

    strategic_results = []
    for title, expected_entities in TEST_TITLES["strategic_with_location"]:
        result = await llm_client.strategic_review(title)
        strategic_results.append((result, expected_entities))

        # Check if strategic
        strategic_ok = result["is_strategic"]

        # Check if at least some expected entities are found
        extracted = result.get("entities", [])
        entity_match = any(
            any(
                exp.lower() in ent.lower() or ent.lower() in exp.lower()
                for exp in expected_entities
            )
            for ent in extracted
        )

        status = "✓ PASS" if (strategic_ok and entity_match) else "✗ FAIL"
        print(f"\n{status}")
        print(f"Title: {title[:80]}")
        print(f"Strategic: {result['is_strategic']}")
        print(f"Expected entities: {expected_entities}")
        print(f"Extracted entities: {extracted}")

    # Calculate accuracy for Group 2
    correct_strategic = sum(
        1
        for r, expected in strategic_results
        if r["is_strategic"] and r.get("entities")
    )
    accuracy_group2 = (correct_strategic / len(strategic_results)) * 100
    print(f"\n{'='*80}")
    print(
        f"GROUP 2 ACCURACY: {correct_strategic}/{len(strategic_results)} = {accuracy_group2:.1f}%"
    )

    # Test Group 4: Incoherent titles (should be strategic=0)
    print("\n" + "=" * 80)
    print("GROUP 4: Incoherent/Meaningless Titles (should be filtered OUT)")
    print("=" * 80)

    incoherent_results = []
    for title in TEST_TITLES["incoherent"]:
        result = await llm_client.strategic_review(title)
        incoherent_results.append(result)

        status = "✓ PASS" if not result["is_strategic"] else "✗ FAIL"
        print(f"\n{status}")
        print(f"Title: {title[:80]}")
        print(f"Strategic: {result['is_strategic']}")
        print(f"Entities: {result.get('entities', [])}")

    # Calculate accuracy for Group 4
    correct_incoherent = sum(1 for r in incoherent_results if not r["is_strategic"])
    accuracy_group4 = (correct_incoherent / len(incoherent_results)) * 100
    print(f"\n{'='*80}")
    print(
        f"GROUP 4 ACCURACY: {correct_incoherent}/{len(incoherent_results)} = {accuracy_group4:.1f}%"
    )

    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print(f"Group 1 (Non-strategic filtering): {accuracy_group1:.1f}%")
    print(f"Group 2 (Entity extraction): {accuracy_group2:.1f}%")
    print(f"Group 4 (Coherence check): {accuracy_group4:.1f}%")

    total_correct = correct_non_strategic + correct_strategic + correct_incoherent
    total_tests = (
        len(non_strategic_results) + len(strategic_results) + len(incoherent_results)
    )
    overall_accuracy = (total_correct / total_tests) * 100
    print(
        f"\nOVERALL ACCURACY: {total_correct}/{total_tests} = {overall_accuracy:.1f}%"
    )
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_prompt_improvements())
