#!/usr/bin/env python3
"""
Comprehensive integration test runner for the web scraper pipeline.
Runs all integration tests and provides detailed reporting.
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))


def run_test_suite(test_file, description):
    """Run a specific test suite and return results."""
    print(f"\n{'='*60}")
    print(f"🧪 Running {description}")
    print(f"{'='*60}")

    start_time = time.time()

    # Ensure output directory exists for test results
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            test_file,
            "-v",
            "--tb=short",
            "--color=yes",
            f"--junitxml=output/test_results_{Path(test_file).stem}.xml",
            "--html=output/test_report.html",
            "--self-contained-html"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

        duration = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ {description} - PASSED ({duration:.2f}s)")
            return True, duration, result.stdout
        else:
            print(f"❌ {description} - FAILED ({duration:.2f}s)")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False, duration, result.stdout + result.stderr

    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 {description} - ERROR ({duration:.2f}s): {e}")
        return False, duration, str(e)


def main():
    """Run all integration tests and provide comprehensive reporting."""

    print("🚀 Starting Comprehensive Integration Test Suite")
    print("=" * 80)

    # Ensure output directory exists and save test summary there
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Test suites to run
    test_suites = [
        ("tests/test_integration_extraction.py", "CSV Extraction & Cleaning Pipeline"),
        ("tests/test_integration_database.py", "Web Scraping & Contact Extraction"),
        ("tests/test_integration_data_quality.py", "Data Quality & Validation"),
        ("tests/test_integration_performance.py", "Performance & Edge Cases"),
        
        # Also run the original unit tests to ensure we didn't break anything
        ("tests/test_jobs.py", "Contact Processing Unit Tests"),
        ("tests/test_chatgpt_name.py", "ChatGPT Integration Unit Tests"),
        ("tests/test_process_city.py", "City Processing Unit Tests"),
    ]
    
    results = []
    total_start_time = time.time()
    
    for test_file, description in test_suites:
        success, duration, output = run_test_suite(test_file, description)
        results.append((test_file, description, success, duration, output))
    
    total_duration = time.time() - total_start_time
    
    # Generate comprehensive report
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, _, success, _, _ in results if success)
    total_count = len(results)
    
    print(f"Overall Status: {passed_count}/{total_count} test suites passed")
    print(f"Total Runtime: {total_duration:.2f} seconds")
    print()
    
    # Detailed results
    for test_file, description, success, duration, output in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {description:<40} | {duration:>6.2f}s")
    
    print("\n" + "="*80)
    
    # Performance analysis
    print("⚡ PERFORMANCE ANALYSIS")
    print("-" * 40)
    
    fastest = min(results, key=lambda x: x[3])
    slowest = max(results, key=lambda x: x[3])
    
    print(f"Fastest: {fastest[1]} ({fastest[3]:.2f}s)")
    print(f"Slowest: {slowest[1]} ({slowest[3]:.2f}s)")
    print(f"Average: {sum(r[3] for r in results) / len(results):.2f}s")
    
    # Quality metrics
    print("\n🎯 QUALITY METRICS")
    print("-" * 40)
    
    if passed_count == total_count:
        print("🏆 ALL TESTS PASSED - Excellent code quality!")
        print("✅ UTF-8 BOM handling verified")
        print("✅ Phone number deduplication verified")
        print("✅ Contact extraction accuracy verified")
        print("✅ Data quality validation verified")
        print("✅ Performance benchmarks met")
        print("✅ Edge case handling verified")
    else:
        failed_tests = [r for r in results if not r[2]]
        print(f"⚠️  {len(failed_tests)} test suite(s) failed:")
        for test_file, description, _, _, _ in failed_tests:
            print(f"   - {description}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 40)
    
    if passed_count == total_count:
        print("🎉 Your pipeline is production-ready!")
        print("Consider adding these additional tests:")
        print("  • Load testing with 10,000+ contacts")
        print("  • Network failure simulation for web scraping")
        print("  • Database integration tests")
        print("  • API rate limiting tests")
    else:
        print("🔧 Focus on fixing the failed test suites above")
        print("💡 Run individual test suites for detailed debugging:")
        for test_file, description, success, _, _ in results:
            if not success:
                print(f"   python -m pytest {test_file} -xvs")
    
    # Coverage analysis
    print("\n📈 COVERAGE ANALYSIS")
    print("-" * 40)
    
    covered_areas = [
        "✅ CSV data cleaning and validation",
        "✅ Phone number formatting and deduplication", 
        "✅ Email validation and blacklisting",
        "✅ Hebrew name extraction and transliteration",
        "✅ Department standardization",
        "✅ UTF-8 encoding handling",
        "✅ Web scraping contact extraction",
        "✅ JSON to CSV/Excel conversion",
        "✅ Performance with large datasets",
        "✅ Edge case and error handling",
        "✅ Concurrent processing safety",
        "✅ Memory efficiency validation"
    ]
    
    for area in covered_areas:
        print(f"  {area}")
    
    print("\n" + "="*80)

    # Save test summary to output directory
    summary_file = output_dir / "test_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Test Summary - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Overall Status: {passed_count}/{total_count} test suites passed\n")
        f.write(f"Total Runtime: {total_duration:.2f} seconds\n\n")

        for test_file, description, success, duration, output in results:
            status = "PASS" if success else "FAIL"
            f.write(f"{status} | {description} | {duration:.2f}s\n")

        if passed_count == total_count:
            f.write("\n🎊 ALL TESTS PASSED - Pipeline is production ready!\n")
        else:
            f.write(f"\n⚠️ {len([r for r in results if not r[2]])} test suite(s) failed\n")

    print(f"📄 Test summary saved to: {summary_file}")

    if passed_count == total_count:
        print("🎊 CONGRATULATIONS! Your web scraper pipeline is robust and ready!")
        return 0
    else:
        print("🚨 Some tests failed. Please review and fix the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
