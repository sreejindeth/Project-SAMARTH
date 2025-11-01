"""
Test script to verify all sample prompts work correctly.
"""
import sys
import yaml
from pathlib import Path
from app.question_parser import parse_question
from app.analytics import AnalyticsEngine
from app.data_manager import DataManager

# Sample prompts from README and frontend (all official prompts)
SAMPLE_PROMPTS = [
    # Frontend prompts
    "Compare the average annual rainfall in Karnataka and Maharashtra for the last 5 years. List the top 3 most produced crops of Maize in each of those states during the same period.",
    "Which districts in Tamil Nadu and Kerala had the highest and lowest production of Rice in 2021?",
    "Show the production trend of Wheat in Punjab over the last 5 years and compare it with the rainfall trend.",
    "Should we promote millet over sugarcane in Maharashtra? Give policy arguments using climate data.",
    # README prompts (with full details)
    "Compare the average annual rainfall in Karnataka and Maharashtra for the last 5 years. In parallel, list the top 3 most produced crops of Maize in each of those states during the same period, citing all data sources.",
    "Identify the district in Karnataka with the highest production of Maize in the most recent year available and compare that with the district with the lowest production of Maize in Maharashtra.",
    "Analyze the production trend of Maize in Karnataka over the last 5 years. Correlate this trend with the corresponding climate data for the same period and provide a summary of the apparent impact.",
    "A policy advisor is proposing a scheme to promote Maize over Paddy in Karnataka. Based on historical data from the last 5 years, what are the three most compelling data-backed arguments to support this policy?",
]

def test_prompt(prompt: str, dm: DataManager, engine: AnalyticsEngine):
    """Test a single prompt."""
    print(f"\n{'='*80}")
    print(f"Testing: {prompt}")
    print(f"{'='*80}")

    try:
        # Parse the question
        parsed = parse_question(prompt)
        print(f"✓ Parsed intent: {parsed.intent}")
        print(f"  Parameters: {parsed.params}")

        # Try to execute based on intent
        if parsed.intent == "compare_rainfall_and_crops":
            result = engine.compare_rainfall_and_crops(
                state_a=parsed.params.get("state_a"),
                state_b=parsed.params.get("state_b"),
                crop_filter=parsed.params.get("crop_filter"),
                last_n_years=parsed.params.get("years"),
                top_m=parsed.params.get("top_m", 3),
            )
        elif parsed.intent == "district_extremes":
            result = engine.district_extremes(
                state_a=parsed.params.get("state_a"),
                state_b=parsed.params.get("state_b"),
                crop=parsed.params.get("crop"),
                year=parsed.params.get("year"),
            )
        elif parsed.intent == "production_trend_with_climate":
            result = engine.production_trend_with_climate(
                region=parsed.params.get("region"),
                crop=parsed.params.get("crop"),
                years=parsed.params.get("years"),
            )
        elif parsed.intent == "policy_arguments":
            result = engine.policy_arguments(
                region=parsed.params.get("region"),
                crop_a=parsed.params.get("crop_a"),
                crop_b=parsed.params.get("crop_b"),
                years=parsed.params.get("years"),
            )
        else:
            print(f"✗ Unknown intent: {parsed.intent}")
            return False

        print(f"✓ Successfully executed!")
        print(f"  Answer: {result.answer[:100]}...")
        print(f"  Tables: {len(result.tables)}")
        print(f"  Citations: {len(result.citations)}")
        return True

    except Exception as e:
        print(f"✗ Failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*80)
    print("SAMPLE PROMPT TESTING")
    print("="*80)

    # Load config
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Initialize data manager and engine
    print("\nInitializing analytics engine...")
    dm = DataManager(config)
    engine = AnalyticsEngine(dm)

    # Run tests
    results = []
    for prompt in SAMPLE_PROMPTS:
        success = test_prompt(prompt, dm, engine)
        results.append((prompt, success))

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    success_rate = (passed / total * 100) if total > 0 else 0

    print(f"Total prompts tested: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {success_rate:.1f}%")

    if failed > 0:
        print(f"\nFailed prompts:")
        for prompt, success in results:
            if not success:
                print(f"  - {prompt[:70]}...")

    # Exit with appropriate code
    if success_rate >= 90:
        print(f"\n✓ SUCCESS: Achieved {success_rate:.1f}% success rate (target: 90%)")
        sys.exit(0)
    else:
        print(f"\n✗ FAILED: Only {success_rate:.1f}% success rate (target: 90%)")
        sys.exit(1)


if __name__ == "__main__":
    main()
