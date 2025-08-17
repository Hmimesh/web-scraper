#!/bin/bash
# Test runner that ensures all output goes to the output directory
set -e

echo "🧪 Running Web Scraper Test Suite"
echo "=================================="

# Create output directory if it doesn't exist
mkdir -p output

# Clear previous test results
echo "🧹 Cleaning previous test results..."
rm -f output/test_*.xml output/test_*.html output/test_summary.txt

# Run the comprehensive test suite
echo "🚀 Starting test execution..."
python3 tests/run_integration_tests.py

# Check if test results were created in output directory
echo ""
echo "📁 Test Results Summary:"
echo "========================"

if [ -f "output/test_summary.txt" ]; then
    echo "✅ Test summary: output/test_summary.txt"
    cat output/test_summary.txt
else
    echo "❌ Test summary not found in output directory"
fi

echo ""
echo "📄 Generated test files:"
ls -la output/test_* 2>/dev/null || echo "No test files found in output directory"

echo ""
echo "✅ Test execution completed! All results saved to output/ directory."
