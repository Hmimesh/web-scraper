"""
Integration tests for data quality and end-to-end pipeline validation.
Tests the complete workflow from JSON to CSV/Excel and data quality metrics.
"""

import sys
import os
import tempfile
import json
import pandas as pd
import pytest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import all_contacts
import name_pull
import jobs


class TestDataQualityPipeline:
    """Test data quality throughout the entire processing pipeline."""

    def create_test_json(self, data):
        """Helper to create temporary JSON files for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        return temp_file.name

    def test_json_to_csv_conversion_complete_pipeline(self):
        """Test the complete JSON to CSV/Excel conversion pipeline."""
        
        # Realistic JSON data structure
        test_data = {
            "תל אביב": {
                "דוד כהן": {
                    "שם": "דוד כהן",
                    "תפקיד": "מנהל מחלקת חינוך",
                    "מחלקה": "מחלקת חינוך",
                    "רשות": "תל אביב",
                    "מייל": "david.cohen@telaviv.gov.il",
                    "טלפון פרטי": "052-123-4567",
                    "טלפון משרד": "03-1234567"
                },
                "רחל לוי": {
                    "שם": "רחל לוי",
                    "תפקיד": "מזכירה",
                    "מחלקה": "מחלקת חינוך",
                    "רשות": "תל אביב",
                    "מייל": "rachel@telaviv.gov.il",
                    "טלפון משרד": "03-1234568"
                }
            },
            "חיפה": {
                "יוסי אברהם": {
                    "שם": "יוסי אברהם",
                    "תפקיד": "רכז נוער",
                    "מחלקה": "מחלקת נוער",
                    "רשות": "חיפה",
                    "מייל": "yossi@haifa.gov.il",
                    "טלפון פרטי": "054-111-2222"
                }
            },
            "ירושלים": {
                "מרים דוד": {
                    "שם": "מרים דוד",
                    "תפקיד": "עובדת סוציאלית",
                    "מחלקה": "מחלקת רווחה",
                    "רשות": "ירושלים",
                    "מייל": "miriam@jerusalem.gov.il",
                    "טלפון פרטי": "050-777-8888",
                    "טלפון משרד": "02-5555555"
                }
            }
        }

        json_file = self.create_test_json(test_data)
        
        try:
            # Test the conversion
            all_contacts.main(json_file)
            
            # Check that CSV file was created
            csv_file = "contacts_" + Path(json_file).stem + ".csv"
            excel_file = "contacts_" + Path(json_file).stem + ".xlsx"
            
            assert os.path.exists(csv_file), "CSV file should be created"
            assert os.path.exists(excel_file), "Excel file should be created"
            
            # Load and validate CSV content
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            
            # Basic structure validation
            expected_columns = ['עיר', 'שם', 'טלפון', 'אימייל', 'תפקיד', 'מחלקה']
            for col in expected_columns:
                assert col in df.columns, f"Column {col} should exist"
            
            # Data validation
            assert len(df) == 4, f"Should have 4 contacts, got {len(df)}"
            
            # Check cities
            cities = set(df['עיר'].tolist())
            expected_cities = {'תל אביב', 'חיפה', 'ירושלים'}
            assert cities == expected_cities, f"Cities mismatch: {cities} vs {expected_cities}"
            
            # Check Hebrew preservation
            hebrew_names = df['שם'].tolist()
            for name in hebrew_names:
                assert any(c in name for c in 'אבגדהוזחטיכלמנסעפצקרשת'), f"Hebrew lost in {name}"
            
            # Check phone number formatting
            phones = df['טלפון'].dropna().tolist()
            for phone in phones:
                if phone:  # Skip empty strings
                    assert phone.startswith('0'), f"Phone {phone} should start with 0"
            
            # Check email validity
            emails = df['אימייל'].dropna().tolist()
            for email in emails:
                if email:  # Skip empty strings
                    assert '@' in email and '.' in email, f"Invalid email: {email}"
            
        finally:
            # Cleanup
            os.unlink(json_file)
            for file in [csv_file, excel_file]:
                if os.path.exists(file):
                    os.unlink(file)

    def test_data_quality_metrics_validation(self):
        """Test comprehensive data quality metrics across the pipeline."""
        
        # Create test data with various quality issues
        test_data = {
            "עיר בדיקה": {
                "דוד כהן": {
                    "שם": "דוד כהן",
                    "מייל": "david@test.gov.il",
                    "טלפון פרטי": "052-123-4567",
                    "מחלקה": "מחלקת חינוך"
                },
                "רחל לוי": {
                    "שם": "רחל לוי", 
                    "מייל": "rachel@test.gov.il",
                    "טלפון משרד": "03-1234567",
                    "מחלקה": "מחלקת רווחה"
                },
                "יוסי אברהם": {
                    "שם": "יוסי אברהם",
                    "מייל": "yossi@test.gov.il",
                    # No phone number
                    "מחלקה": "מחלקת נוער"
                },
                "מרים דוד": {
                    "שם": "מרים דוד",
                    "טלפון פרטי": "054-777-8888",
                    # No email
                    "מחלקה": "מחלקת תרבות"
                },
                # Contact with both phone and email
                "אחמד עלי": {
                    "שם": "אחמד עלי",
                    "מייל": "ahmad@test.gov.il",
                    "טלפון פרטי": "050-999-8888",
                    "טלפון משרד": "04-1111111",
                    "מחלקה": "מחלקת ספורט"
                }
            }
        }

        json_file = self.create_test_json(test_data)
        
        try:
            all_contacts.main(json_file)
            csv_file = "contacts_" + Path(json_file).stem + ".csv"
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            
            # Quality metrics
            total_contacts = len(df)
            contacts_with_phone = df['טלפון'].notna().sum()
            contacts_with_email = df['אימייל'].notna().sum()
            contacts_with_both = (df['טלפון'].notna() & df['אימייל'].notna()).sum()
            contacts_with_department = df['מחלקה'].notna().sum()
            
            # Validate quality metrics
            assert total_contacts == 5, f"Expected 5 contacts, got {total_contacts}"
            assert contacts_with_phone >= 3, f"Expected at least 3 with phone, got {contacts_with_phone}"
            assert contacts_with_email >= 3, f"Expected at least 3 with email, got {contacts_with_email}"
            assert contacts_with_both >= 2, f"Expected at least 2 with both, got {contacts_with_both}"
            assert contacts_with_department == 5, f"All should have departments, got {contacts_with_department}"
            
            # Check for data completeness
            completeness_score = (contacts_with_phone + contacts_with_email) / (total_contacts * 2)
            assert completeness_score >= 0.7, f"Data completeness too low: {completeness_score}"
            
        finally:
            os.unlink(json_file)
            csv_file = "contacts_" + Path(json_file).stem + ".csv"
            if os.path.exists(csv_file):
                os.unlink(csv_file)

    def test_name_extraction_and_transliteration_quality(self, monkeypatch):
        """Test the quality of name extraction and Hebrew transliteration."""

        # Mock the transliteration function to return predictable results
        def mock_transliterate(name):
            translations = {
                "David Cohen": "דוד כהן",
                "Sarah Levy": "שרה לוי",
                "Ahmad Ali": "אחמד עלי"
            }
            return translations.get(name, name)

        monkeypatch.setattr(jobs, "guess_hebrew_name", mock_transliterate)

        # Test various name scenarios
        test_cases = [
            ("David Cohen manager", True),  # Should extract name
            ("Sarah Levy secretary", True),  # Should extract name
            ("דוד כהן מנהל", True),  # Already Hebrew
            ("info@city.gov.il", False),  # Should be filtered
            ("webmaster contact", False),  # Should be filtered
            ("Ahmad Ali coordinator", True),  # Should extract name
        ]

        for input_text, should_have_valid_name in test_cases:
            contact = jobs.Contacts(input_text, "עיר בדיקה")

            if should_have_valid_name:
                # Should have extracted a valid name (not filtered)
                assert contact.name != "לא נמצא שם" and not contact.name.startswith("לא נמצא"), \
                    f"Input '{input_text}' should extract valid name, got '{contact.name}'"
            else:
                # Should be filtered out
                assert contact.name == "לא נמצא שם" or contact.name.startswith("לא נמצא"), \
                    f"Input '{input_text}' should be filtered, got '{contact.name}'"

    def test_department_standardization_quality(self):
        """Test the quality of department name standardization."""
        
        test_cases = [
            ("education department", "מחלקת חינוך"),
            ("youth coordinator", "מחלקת נוער"),
            ("welfare office", "מחלקת רווחה"),
            ("culture events", "מחלקת תרבות"),
            ("sports activities", "מחלקת ספורט"),
            ("מחלקת חינוך", "מחלקת חינוך"),  # Already Hebrew
        ]
        
        for input_text, expected_dept_type in test_cases:
            contact = jobs.Contacts(input_text, "עיר בדיקה")
            
            if contact.department:
                # Should contain Hebrew department structure
                assert any(word in contact.department for word in ['מחלקת', 'אגף']), \
                    f"Department should be standardized: '{contact.department}' from '{input_text}'"

    def test_phone_number_quality_comprehensive(self):
        """Test comprehensive phone number quality validation."""
        
        test_phone_numbers = [
            ("052-123-4567", True, "052-123-4567"),  # Already formatted
            ("0521234567", True, "052-123-4567"),    # Should be formatted
            ("+972-52-123-4567", True, "052-123-4567"),  # International
            ("972521234567", True, "052-123-4567"),   # International no spaces
            ("03-1234567", True, "03-123-4567"),      # Landline
            ("invalid-phone", False, None),           # Invalid
            ("", False, None),                        # Empty
            ("123", False, None),                     # Too short
        ]
        
        for input_phone, should_be_valid, expected_format in test_phone_numbers:
            from extraction import clean_phone_number
            result = clean_phone_number(input_phone)
            
            if should_be_valid:
                assert result is not None, f"Phone '{input_phone}' should be valid"
                assert result == expected_format, f"Phone '{input_phone}' should format to '{expected_format}', got '{result}'"
                assert result.startswith('0'), f"Formatted phone should start with 0: '{result}'"
                assert '-' in result, f"Formatted phone should have dashes: '{result}'"
            else:
                assert result is None, f"Phone '{input_phone}' should be invalid, got '{result}'"

    def test_email_quality_validation(self):
        """Test email address quality validation."""
        
        test_emails = [
            ("david@city.gov.il", True),
            ("rachel.levy@municipality.org", True),
            ("info@city.gov.il", True),  # Valid format but might be filtered by name
            ("invalid-email", False),
            ("@missing-local.com", False),
            ("missing-domain@", False),
            ("", False),
            ("user@domain", False),  # Missing TLD
        ]
        
        for input_email, should_be_valid in test_emails:
            from extraction import clean_email
            result = clean_email(input_email)
            
            if should_be_valid:
                assert result is not None, f"Email '{input_email}' should be valid"
                assert '@' in result, f"Valid email should contain @: '{result}'"
                assert '.' in result, f"Valid email should contain domain: '{result}'"
            else:
                assert result is None, f"Email '{input_email}' should be invalid, got '{result}'"

    def test_duplicate_detection_comprehensive(self):
        """Test comprehensive duplicate detection across different scenarios."""
        
        # Test data with various duplicate scenarios
        test_data = [
            {'שם': 'דוד כהן', 'טלפון': '052-123-4567', 'אימייל': 'david@test.com', 'עיר': 'תל אביב'},
            {'שם': 'דוד כהן', 'טלפון': '0521234567', 'אימייל': 'david@test.com', 'עיר': 'תל אביב'},  # Same phone different format
            {'שם': 'רחל לוי', 'טלפון': '054-111-2222', 'אימייל': 'rachel@test.com', 'עיר': 'חיפה'},
            {'שם': 'רחל לוי אחרת', 'טלפון': '054-111-2222', 'אימייל': 'rachel2@test.com', 'עיר': 'חיפה'},  # Same phone different email
            {'שם': 'יוסי אברהם', 'טלפון': '053-333-4444', 'אימייל': 'yossi@test.com', 'עיר': 'ירושלים'},
            {'שם': 'יוסי אברהם', 'טלפון': '053-555-6666', 'אימייל': 'yossi@test.com', 'עיר': 'ירושלים'},  # Same email different phone
        ]
        
        # Create temporary CSV
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig')
        df = pd.DataFrame(test_data)
        df.to_csv(temp_file.name, index=False, encoding='utf-8-sig')
        temp_file.close()
        
        output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
        
        try:
            from extraction import clean_csv_data
            clean_csv_data(temp_file.name, output_file, use_openai=False)
            
            result_df = pd.read_csv(output_file, encoding='utf-8-sig')
            
            # Should have fewer contacts due to deduplication
            assert len(result_df) < len(test_data), "Should remove duplicates"
            
            # Check that no duplicate phone numbers remain
            phones = result_df['טלפון'].dropna()
            unique_phones = phones.nunique()
            total_phones = len(phones)
            
            assert unique_phones == total_phones, f"Should have no duplicate phones: {phones.value_counts()}"
            
        finally:
            os.unlink(temp_file.name)
            os.unlink(output_file)
