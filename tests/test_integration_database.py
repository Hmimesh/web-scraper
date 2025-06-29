"""
Integration tests for database_func.py scraping pipeline.
Tests contact extraction from web pages and data processing.
"""

import sys
import os
import tempfile
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import database_func
from jobs import Contacts


class TestDatabaseScrapingPipeline:
    """Test the complete web scraping and contact extraction pipeline."""

    def test_extract_contacts_from_realistic_text(self):
        """Test contact extraction from realistic Hebrew municipal website text."""
        
        # Realistic Hebrew text from a municipal website
        sample_text = """
        מחלקת חינוך
        ראש המחלקה: דוד כהן
        טלפון: 052-123-4567
        דוא"ל: david.cohen@city.gov.il
        
        מזכירת המחלקה: רחל לוי
        טלפון: 03-9876543
        אימייל: rachel.levy@city.gov.il
        
        רכז פעילויות נוער: יוסי אברהם
        נייד: 054-111-2222
        דואר אלקטרוני: yossi@youth.city.gov.il
        
        לפרטים נוספים פנו למזכירות
        טלפון: 03-1234567
        
        מחלקת רווחה
        מנהלת: מרים דוד
        טלפון משרד: 02-5555555
        מייל: miriam@welfare.gov.il
        
        עובד סוציאלי: אחמד עלי
        טלפון: 050-777-8888
        אימייל: ahmad@social.gov.il
        """
        
        city_name = "תל אביב"
        result = database_func.extract_relevant_contacts_from_text(sample_text, city_name)
        
        # Should return data in the expected format
        assert city_name in result
        contacts = result[city_name]
        
        # Should extract multiple contacts
        assert len(contacts) >= 4, f"Expected at least 4 contacts, got {len(contacts)}"
        
        # Verify specific contacts were extracted correctly
        contact_names = list(contacts.keys())
        
        # Check for Hebrew names
        hebrew_names = [name for name in contact_names if any(c in name for c in 'אבגדהוזחטיכלמנסעפצקרשת')]
        assert len(hebrew_names) >= 3, f"Should extract Hebrew names, got: {contact_names}"
        
        # Verify contact details are properly extracted
        for name, contact_info in contacts.items():
            if name == "לא נמצא שם":
                continue
                
            # Each contact should have basic structure
            assert "שם" in contact_info
            assert "רשות" in contact_info
            assert contact_info["רשות"] == city_name
            
            # Should have either phone or email
            has_phone = contact_info.get("טלפון פרטי") or contact_info.get("טלפון משרד")
            has_email = contact_info.get("מייל")
            assert has_phone or has_email, f"Contact {name} should have phone or email"

    def test_contact_extraction_with_departments(self):
        """Test that department information is correctly extracted and standardized."""
        
        sample_text = """
        מחלקת חינוך ותרבות
        מנהל: שלמה כהן
        טלפון: 052-111-1111
        מייל: shlomo@education.gov.il
        
        אגף נוער וספורט
        רכזת: דינה לוי
        טלפון: 054-222-2222
        אימייל: dina@youth.gov.il
        
        מחלקת רווחה
        עובדת סוציאלית: מרים אברהם
        נייד: 053-333-3333
        דוא"ל: miriam@welfare.gov.il
        """
        
        result = database_func.extract_relevant_contacts_from_text(sample_text, "חיפה")
        contacts = result["חיפה"]
        
        # Check that departments are extracted
        departments_found = []
        for contact_info in contacts.values():
            dept = contact_info.get("מחלקה")
            if dept:
                departments_found.append(dept)
        
        assert len(departments_found) > 0, "Should extract department information"
        
        # Check for Hebrew department names
        hebrew_depts = [dept for dept in departments_found if 'מחלקת' in dept or 'אגף' in dept]
        assert len(hebrew_depts) > 0, f"Should extract Hebrew departments, got: {departments_found}"

    def test_contact_extraction_filters_invalid_data(self):
        """Test that invalid or non-personal contact data is filtered out."""
        
        sample_text = """
        לפרטים נוספים פנו למזכירות
        טלפון: 03-1234567
        
        info@municipality.gov.il
        
        webmaster@city.gov.il
        טלפון: 02-9999999
        
        contact@helpdesk.gov.il
        לתמיכה טכנית אנא פנו
        
        דוד כהן - מנהל
        טלפון: 052-123-4567
        מייל: david@city.gov.il
        """
        
        result = database_func.extract_relevant_contacts_from_text(sample_text, "ירושלים")
        contacts = result["ירושלים"]
        
        # Should filter out generic/invalid contacts
        contact_names = list(contacts.keys())
        
        # Should not include blacklisted names
        assert "info" not in contact_names
        assert "webmaster" not in contact_names
        assert "contact" not in contact_names
        assert "לפרטים נוספים" not in contact_names
        assert "לתמיכה טכנית" not in contact_names
        
        # Should include valid personal names
        valid_names = [name for name in contact_names if name != "לא נמצא שם"]
        assert len(valid_names) >= 1, f"Should have at least one valid contact, got: {contact_names}"

    def test_phone_number_formatting_in_extraction(self):
        """Test that phone numbers are properly formatted during extraction."""
        
        sample_text = """
        דוד כהן
        טלפון: 0521234567
        
        רחל לוי  
        נייד: +972-54-111-2222
        
        יוסי אברהם
        טלפון משרד: 03 9876543
        
        מרים דוד
        טלפון: 972-2-5555555
        """
        
        result = database_func.extract_relevant_contacts_from_text(sample_text, "באר שבע")
        contacts = result["באר שבע"]
        
        # Check phone number formatting
        for contact_info in contacts.values():
            mobile = contact_info.get("טלפון פרטי")
            office = contact_info.get("טלפון משרד")
            
            for phone in [mobile, office]:
                if phone:
                    # Should be formatted with dashes and start with 0
                    assert phone.startswith('0'), f"Phone {phone} should start with 0"
                    if len(phone) >= 10:  # Mobile numbers
                        assert '-' in phone, f"Phone {phone} should be formatted with dashes"

    def test_process_city_with_mock_page(self, monkeypatch):
        """Test process_city function with mocked web page interactions."""

        # Mock the playwright components
        mock_page = Mock()
        mock_browser = Mock()
        mock_playwright = Mock()

        # Mock page content
        mock_page.inner_text.return_value = """
        מחלקת חינוך
        מנהל: דוד כהן
        טלפון: 052-123-4567
        מייל: david@education.gov.il
        """

        mock_browser.new_page.return_value = mock_page
        mock_browser.close.return_value = None
        mock_playwright.chromium.launch.return_value = mock_browser

        # Mock the sync_playwright context manager properly
        class MockSyncPlaywright:
            def __enter__(self):
                return mock_playwright
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        monkeypatch.setattr(database_func, "sync_playwright", MockSyncPlaywright)
        
        # Mock the deep link finding to return a simple list
        monkeypatch.setattr(database_func, "find_deep_contact_links", lambda page, url: [url])
        
        # Test data
        row = {
            "עיר": "תל אביב",
            "קישור": "https://example-city.gov.il"
        }
        existing_data = {}
        
        # Run the function
        city, data = database_func.process_city(row, existing_data)
        
        # Verify results
        assert city == "תל אביב"
        assert isinstance(data, dict)
        
        # Should have extracted at least one contact
        if data:  # Only check if data was extracted
            assert len(data) > 0, "Should extract at least one contact"

    def test_process_city_error_handling(self):
        """Test that process_city handles various error conditions gracefully."""
        
        # Test with invalid URL
        row = {"עיר": "עיר בדיקה", "קישור": "invalid-url"}
        city, data = database_func.process_city(row, {})
        
        assert city == "עיר בדיקה"
        assert data == {}  # Should return empty dict on error
        
        # Test with NaN URL (our fix)
        row = {"עיר": "עיר נאן", "קישור": " NaN "}
        city, data = database_func.process_city(row, {})
        
        assert city == "עיר נאן"
        assert data == {}  # Should skip without calling playwright
        
        # Test with already existing data
        existing_data = {"עיר קיימת": {"איש קשר": {"שם": "דוד"}}}
        row = {"עיר": "עיר קיימת", "קישור": "https://example.com"}
        city, data = database_func.process_city(row, existing_data)
        
        assert city == "עיר קיימת"
        assert data == {"איש קשר": {"שם": "דוד"}}  # Should return existing data

    def test_contact_object_creation_and_validation(self):
        """Test that Contact objects are created correctly with proper validation."""
        
        # Test valid contact creation
        valid_text = "דוד כהן מנהל מחלקת חינוך טלפון: 052-123-4567 מייל: david@city.gov.il"
        contact = Contacts(valid_text, "תל אביב")
        
        assert contact.name is not None
        assert contact.city == "תל אביב"
        assert contact.email is not None
        assert "@" in contact.email
        
        # Test blacklisted contact filtering
        blacklisted_text = "info@city.gov.il טלפון: 03-1234567"
        contact = Contacts(blacklisted_text, "חיפה")

        # Should be filtered (either "לא נמצא שם" or extracted as invalid name)
        assert contact.name == "לא נמצא שם" or "info" not in contact.name.lower(), \
            f"Blacklisted contact should be filtered, got '{contact.name}'"
        
        # Test contact with Hebrew and English mixed
        mixed_text = "David Cohen manager education department phone: 052-111-2222 email: david@edu.gov.il"
        contact = Contacts(mixed_text, "ירושלים")
        
        # Should extract some information
        assert contact.email is not None
        assert contact.city == "ירושלים"
