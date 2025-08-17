#!/bin/bash
# Post-processing after running main.sh - Production Ready
set -e

# Create output directory if it doesn't exist
mkdir -p output

# Find the most recent CSV file from main.sh output
LATEST_CSV=$(find output -name "all_contacts*.csv" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

if [ -z "$LATEST_CSV" ]; then
    # Fallback to looking for any CSV in current directory
    LATEST_CSV=$(find . -maxdepth 1 -name "all_contacts*.csv" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
fi

if [ -z "$LATEST_CSV" ]; then
    echo "❌ No CSV file found. Please run main.sh first to generate contacts data." >&2
    echo "Expected files like: output/all_contacts.csv or all_contacts.csv" >&2
    exit 1
fi

# Generate output filename based on input
BASENAME=$(basename "$LATEST_CSV" .csv)
OUTPUT="output/extracted_contacts_${BASENAME}.csv"

echo "🔄 Processing: $LATEST_CSV"
echo "📄 Output will be: $OUTPUT"

# Run the extraction with proper error handling
if python3 ./src/extraction.py "$LATEST_CSV" "$OUTPUT"; then
    echo "✅ Post-processing completed successfully!"
    echo "📁 Final cleaned contacts saved to: $OUTPUT"

    # Show file size for verification
    if [ -f "$OUTPUT" ]; then
        SIZE=$(du -h "$OUTPUT" | cut -f1)
        LINES=$(wc -l < "$OUTPUT" 2>/dev/null || echo "unknown")
        echo "📊 File size: $SIZE, Lines: $LINES"
    fi
else
    echo "❌ Post-processing failed. Check the error messages above." >&2
    exit 1
fi
