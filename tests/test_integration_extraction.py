"""
Integration tests for the complete extraction.py pipeline.
Tests the entire CSV cleaning workflow from raw input to final output.
"""

import sys
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import extraction


class TestExtractionPipeline:
    """Test the complete extraction pipeline with realistic data scenarios."""

    def create_test_csv(self, data, encoding='utf-8-sig'):
        """Helper to create temporary CSV files for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding=encoding)
        df = pd.DataFrame(data)
        df.to_csv(temp_file.name, index=False, encoding=encoding)
        temp_file.close()
        return temp_file.name

    def test_complete_pipeline_realistic_data(self, monkeypatch):
        """Test the complete pipeline with realistic messy contact data."""
        # Mock OpenAI to avoid API calls
        monkeypatch.setattr(extraction, "gpt_fix_names_and_department", 
                          lambda name, dept: (name.strip() if name else "", dept.strip() if dept else ""))
        
        # Realistic messy data that mimics real-world scenarios
        test_data = [
            {
                'שם': 'דוד כהן',
                'טלפון': '052-123-4567',
                'אימייל': 'david.cohen@city.gov.il',
                'מחלקה': 'מחלקת חינוך',
                'עיר': 'תל אביב'
            },
            {
                'שם': 'Sarah Smith',  # English name that should be transliterated
                'טלפון': '0521234567',  # No dashes
                'אימייל': 'sarah@municipality.org',
                'מחלקה': 'education',  # English department
                'עיר': 'חיפה'
            },
            {
                'שם': 'info@contact',  # Should be filtered out
                'טלפון': '+972-52-999-8888',  # International format
                'אימייל': 'info@city.gov.il',
                'מחלקה': '',
                'עיר': 'ירושלים'
            },
            {
                'שם': 'מרים לוי',
                'טלפון': '052 111 2222',  # Spaces instead of dashes
                'אימייל': 'miriam.levy@example.com',
                'מחלקה': 'מחלקת רווחה',
                'עיר': 'באר שבע'
            },
            {
                'שם': 'webmaster',  # Blacklisted name
                'טלפון': '03-1234567',
                'אימייל': 'webmaster@site.com',
                'מחלקה': 'IT',
                'עיר': 'רמת גן'
            },
            {
                'שם': 'אחמד עלי',  # Arabic name
                'טלפון': '054-777-8888',
                'אימייל': 'ahmad@council.org',
                'מחלקה': 'מחלקת תרבות',
                'עיר': 'נצרת'
            },
            # Duplicate phone numbers (different formats)
            {
                'שם': 'יוסי דוד',
                'טלפון': '052-123-4567',  # Same as first contact
                'אימייל': 'yossi@different.com',
                'מחלקה': 'מחלקת ספורט',
                'עיר': 'אשדוד'
            },
            # Empty/invalid data
            {
                'שם': '',
                'טלפון': 'invalid-phone',
                'אימייל': 'not-an-email',
                'מחלקה': '',
                'עיר': 'עכו'
            }
        ]

        input_file = self.create_test_csv(test_data)
        output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name

        try:
            # Run the complete pipeline
            extraction.clean_csv_data(input_file, output_file, use_openai=False)
            
            # Verify output file exists and is readable
            assert os.path.exists(output_file)
            
            # Load and verify the cleaned data
            result_df = pd.read_csv(output_file, encoding='utf-8-sig')
            
            # Basic validation
            assert len(result_df) > 0, "Output should contain some valid contacts"
            assert len(result_df) < len(test_data), "Should filter out invalid contacts"
            
            # Check that phone numbers are properly formatted
            valid_phones = result_df['טלפון'].dropna()
            for phone in valid_phones:
                assert '-' in phone, f"Phone {phone} should be formatted with dashes"
                assert phone.startswith('0'), f"Phone {phone} should start with 0"
            
            # Check that emails are valid
            valid_emails = result_df['אימייל'].dropna()
            for email in valid_emails:
                assert '@' in email, f"Email {email} should contain @"
                assert '.' in email, f"Email {email} should contain domain"
            
            # Check that blacklisted names are filtered out
            names = result_df['שם'].tolist()
            assert 'webmaster' not in names, "Blacklisted names should be filtered"
            assert 'info@contact' not in names, "Invalid names should be filtered"
            
            # Check for duplicate phone numbers
            phone_counts = result_df['טלפון'].value_counts()
            duplicates = phone_counts[phone_counts > 1]
            assert len(duplicates) == 0, f"Should not have duplicate phones: {duplicates.to_dict()}"
            
            # Verify UTF-8 encoding works
            hebrew_names = [name for name in names if any(c in name for c in 'אבגדהוזחטיכלמנסעפצקרשת')]
            assert len(hebrew_names) > 0, "Should preserve Hebrew names"
            
        finally:
            # Cleanup
            os.unlink(input_file)
            os.unlink(output_file)

    def test_phone_number_deduplication_aggressive(self):
        """Test that phone number deduplication really puts its foot down."""
        test_data = [
            {'שם': 'איש א', 'טלפון': '052-123-4567', 'אימייל': 'a@test.com', 'עיר': 'עיר א'},
            {'שם': 'איש ב', 'טלפון': '0521234567', 'אימייל': 'b@test.com', 'עיר': 'עיר ב'},  # Same phone, no dashes
            {'שם': 'איש ג', 'טלפון': '+972-52-123-4567', 'אימייל': 'c@test.com', 'עיר': 'עיר ג'},  # International
            {'שם': 'איש ד', 'טלפון': '972521234567', 'אימייל': 'd@test.com', 'עיר': 'עיר ד'},  # International no spaces
            {'שם': 'איש ה', 'טלפון': '052 123 4567', 'אימייל': 'e@test.com', 'עיר': 'עיר ה'},  # Spaces
        ]

        input_file = self.create_test_csv(test_data)
        output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name

        try:
            extraction.clean_csv_data(input_file, output_file, use_openai=False)
            result_df = pd.read_csv(output_file, encoding='utf-8-sig')
            
            # Should only have ONE contact remaining (all others are duplicates)
            assert len(result_df) == 1, f"Expected 1 contact, got {len(result_df)}. All phones are the same!"
            
            # The remaining phone should be properly formatted
            remaining_phone = result_df.iloc[0]['טלפון']
            assert remaining_phone == '052-123-4567', f"Expected formatted phone, got {remaining_phone}"
            
        finally:
            os.unlink(input_file)
            os.unlink(output_file)

    def test_utf8_bom_encoding_handling(self):
        """Test that UTF-8 BOM encoding is handled correctly to prevent gibberish."""
        test_data = [
            {'שם': 'משה כהן', 'טלפון': '052-111-2222', 'אימייל': 'moshe@test.co.il', 'עיר': 'תל אביב'},
            {'שם': 'פטמה חליל', 'טלפון': '054-333-4444', 'אימייל': 'fatma@test.org', 'עיר': 'נצרת'},
            {'שם': 'יוחנן ברכה', 'טלפון': '053-555-6666', 'אימייל': 'yohanan@test.net', 'עיר': 'ירושלים'},
        ]

        # Test with different encodings
        for encoding in ['utf-8-sig', 'utf-8', 'cp1255']:
            input_file = self.create_test_csv(test_data, encoding=encoding)
            output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name

            try:
                # Should handle any of these encodings
                extraction.clean_csv_data(input_file, output_file, use_openai=False)
                
                # Output should always be UTF-8 with BOM
                result_df = pd.read_csv(output_file, encoding='utf-8-sig')
                
                # Verify Hebrew characters are preserved
                hebrew_names = result_df['שם'].tolist()
                for name in hebrew_names:
                    assert any(c in name for c in 'אבגדהוזחטיכלמנסעפצקרשת'), f"Hebrew lost in {name}"
                
                # Verify cities are preserved
                cities = result_df['עיר'].tolist()
                assert 'תל אביב' in cities, "Hebrew city names should be preserved"
                assert 'ירושלים' in cities, "Hebrew city names should be preserved"
                
            finally:
                os.unlink(input_file)
                os.unlink(output_file)

    def test_openai_integration_mock(self, monkeypatch):
        """Test OpenAI integration with mocked responses."""
        # Mock the OpenAI function to return predictable results
        def mock_gpt_fix(name, dept):
            if name == "David":
                return "דוד", "מחלקת חינוך"
            elif name == "Sarah":
                return "שרה", "מחלקת תרבות"
            return name, dept

        monkeypatch.setattr(extraction, "gpt_fix_names_and_department", mock_gpt_fix)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        test_data = [
            {'שם': 'David', 'טלפון': '052-111-2222', 'אימייל': 'david@test.com', 'מחלקה': 'education', 'עיר': 'תל אביב'},
            {'שם': 'Sarah', 'טלפון': '053-333-4444', 'אימייל': 'sarah@test.com', 'מחלקה': 'culture', 'עיר': 'חיפה'},
        ]

        input_file = self.create_test_csv(test_data)
        output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name

        try:
            # Run with OpenAI enabled
            extraction.clean_csv_data(input_file, output_file, use_openai=True)
            result_df = pd.read_csv(output_file, encoding='utf-8-sig')
            
            # Verify OpenAI transformations were applied
            names = result_df['שם'].tolist()
            assert 'דוד' in names, "David should be translated to דוד"
            assert 'שרה' in names, "Sarah should be translated to שרה"
            
            departments = result_df['מחלקה'].tolist()
            assert 'מחלקת חינוך' in departments, "Education should be translated"
            assert 'מחלקת תרבות' in departments, "Culture should be translated"
            
        finally:
            os.unlink(input_file)
            os.unlink(output_file)
