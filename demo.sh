#!/bin/bash
# 🎬 DEMONSTRATION SCRIPT - Web Scraper Pipeline
# This script demonstrates the complete workflow from testing to production

set -e

echo "🎬 WEB SCRAPER PIPELINE DEMONSTRATION"
echo "====================================="
echo ""

# Function to show step with nice formatting
show_step() {
    echo ""
    echo "🔹 STEP $1: $2"
    echo "$(printf '%.0s-' {1..50})"
}

# Function to pause for demonstration
demo_pause() {
    echo ""
    read -p "👆 Press Enter to continue to next step..."
    echo ""
}

show_step "1" "Testing the Pipeline"
echo "First, let's run our comprehensive test suite to ensure everything works:"
echo "Command: ./test.sh"
demo_pause

# Run tests
./test.sh

show_step "2" "Main Scraping Process"
echo "Now let's run the main scraping process with a demo filename:"
echo "This will scrape municipal websites and create contact data."
echo ""
echo "Command: ./main.sh"
echo "We'll use filename: demo_contacts"
demo_pause

# Run main process with demo input
echo "demo_contacts" | ./main.sh

show_step "3" "Post-Processing with After_main.sh"
echo "Finally, let's run the post-processing to clean and enhance the data:"
echo "This will find the latest CSV and apply OpenAI cleaning."
echo ""
echo "Command: ./After_main.sh"
demo_pause

# Run after_main
./After_main.sh

show_step "4" "Results Summary"
echo "Let's see what we've created:"
echo ""

echo "📁 Output Directory Contents:"
ls -la output/ | grep -E "\.(json|csv|xlsx|txt|xml|html)$" || echo "No output files found"

echo ""
echo "📊 File Sizes:"
du -h output/*.{json,csv,xlsx} 2>/dev/null | head -10 || echo "No data files found"

echo ""
echo "🎯 Key Files Created:"
echo "  • JSON data: output/contacts_demo_contacts.json"
echo "  • CSV export: output/all_contacts.csv" 
echo "  • Excel export: output/all_contacts.xlsx"
echo "  • Cleaned data: output/extracted_contacts_*.csv"
echo "  • Test results: output/test_summary.txt"

echo ""
echo "🎊 DEMONSTRATION COMPLETE!"
echo "=========================="
echo ""
echo "💡 What just happened:"
echo "  1. ✅ Ran comprehensive tests (results in output/)"
echo "  2. 🕷️  Scraped municipal websites for contacts"
echo "  3. 🧹 Applied AI-powered data cleaning"
echo "  4. 📄 Generated multiple output formats"
echo ""
echo "🚀 Your pipeline is now ready for production!"
echo "   All outputs are organized in the output/ directory."
echo ""
echo "📖 Next steps:"
echo "  • Review output/test_summary.txt for test results"
echo "  • Check output/extracted_contacts_*.csv for final data"
echo "  • Use output/all_contacts.xlsx for Excel analysis"
