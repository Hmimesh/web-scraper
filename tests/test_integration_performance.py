"""
Performance and edge case tests for the complete processing pipeline.
Tests scalability, error handling, and boundary conditions.
"""

import sys
import os
import tempfile
import time
import pandas as pd
import pytest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import extraction
import jobs
from jobs import Contacts


class TestPerformanceAndEdgeCases:
    """Test performance characteristics and edge case handling."""

    def test_large_dataset_processing_performance(self, monkeypatch):
        """Test processing performance with a large dataset."""
        
        # Mock OpenAI to avoid API calls
        monkeypatch.setattr(extraction, "gpt_fix_names_and_department", 
                          lambda name, dept: (name, dept))
        
        # Generate large test dataset
        large_dataset = []
        for i in range(1000):  # 1000 contacts
            large_dataset.append({
                'שם': f'איש קשר {i}',
                'טלפון': f'052-{i:03d}-{(i*7)%10000:04d}',
                'אימייל': f'contact{i}@city{i%10}.gov.il',
                'מחלקה': f'מחלקת {["חינוך", "רווחה", "תרבות", "ספורט", "נוער"][i%5]}',
                'עיר': f'עיר {i%20}'
            })
        
        # Create temporary CSV
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig')
        df = pd.DataFrame(large_dataset)
        df.to_csv(temp_file.name, index=False, encoding='utf-8-sig')
        temp_file.close()
        
        output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
        
        try:
            # Measure processing time
            start_time = time.time()
            extraction.clean_csv_data(temp_file.name, output_file, use_openai=False)
            processing_time = time.time() - start_time
            
            # Performance assertions
            assert processing_time < 30, f"Processing 1000 contacts took too long: {processing_time:.2f}s"
            
            # Verify output
            result_df = pd.read_csv(output_file, encoding='utf-8-sig')
            assert len(result_df) > 900, f"Should retain most contacts, got {len(result_df)}"
            
            # Check memory efficiency - result should be reasonable size
            file_size = os.path.getsize(output_file)
            assert file_size < 1024 * 1024, f"Output file too large: {file_size} bytes"
            
        finally:
            os.unlink(temp_file.name)
            os.unlink(output_file)

    def test_malformed_data_handling(self):
        """Test handling of various malformed and edge case data."""
        
        malformed_data = [
            # Missing required fields
            {'שם': '', 'טלפון': '', 'אימייל': '', 'עיר': 'עיר ריקה'},
            
            # Extremely long values
            {'שם': 'א' * 1000, 'טלפון': '052-123-4567', 'אימייל': 'long@test.com', 'עיר': 'עיר ארוכה'},
            
            # Special characters and encoding issues
            {'שם': 'דוד\x00כהן', 'טלפון': '052-123-4567', 'אימייל': 'special@test.com', 'עיר': 'עיר מיוחדת'},
            
            # Mixed languages
            {'שם': 'David דוד Cohen כהן', 'טלפון': '052-123-4567', 'אימייל': 'mixed@test.com', 'עיר': 'Mixed עיר'},
            
            # Numbers in names
            {'שם': 'דוד123כהן456', 'טלפון': '052-123-4567', 'אימייל': 'numbers@test.com', 'עיר': 'עיר מספרים'},
            
            # SQL injection attempts
            {'שם': "'; DROP TABLE contacts; --", 'טלפון': '052-123-4567', 'אימייל': 'sql@test.com', 'עיר': 'עיר SQL'},
            
            # Unicode edge cases
            {'שם': '🙂😀👍', 'טלפון': '052-123-4567', 'אימייל': 'emoji@test.com', 'עיר': 'עיר אמוג\'י'},
            
            # Valid data for comparison (clearly valid contact)
            {'שם': 'דוד כהן', 'טלפון': '052-123-4567', 'אימייל': 'david@test.com', 'עיר': 'עיר תקינה'},
            {'שם': 'רחל לוי', 'טלפון': '054-111-2222', 'אימייל': 'rachel@test.com', 'עיר': 'עיר נוספת'},
        ]
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig')
        df = pd.DataFrame(malformed_data)
        df.to_csv(temp_file.name, index=False, encoding='utf-8-sig')
        temp_file.close()
        
        output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
        
        try:
            # Should not crash on malformed data
            extraction.clean_csv_data(temp_file.name, output_file, use_openai=False)
            
            # Verify output exists and is readable
            assert os.path.exists(output_file)
            result_df = pd.read_csv(output_file, encoding='utf-8-sig')
            
            # Should filter out most malformed data but keep valid entries
            assert len(result_df) >= 1, "Should keep at least the valid contact"
            assert len(result_df) < len(malformed_data), "Should filter out malformed data"
            
            # Check that valid data is preserved
            valid_names = result_df['שם'].tolist()
            # Should have at least one valid Hebrew name (might not be exactly 'דוד כהן' due to cleaning)
            hebrew_names = [name for name in valid_names if any(c in name for c in 'אבגדהוזחטיכלמנסעפצקרשת')]
            assert len(hebrew_names) >= 1, f"Should preserve at least one Hebrew name, got: {valid_names}"
            
        finally:
            os.unlink(temp_file.name)
            os.unlink(output_file)

    def test_encoding_edge_cases(self):
        """Test various encoding scenarios and edge cases."""
        
        # Test data with various encoding challenges
        encoding_test_data = [
            {'שם': 'דוד כהן', 'טלפון': '052-123-4567', 'אימייל': 'david@test.co.il', 'עיר': 'תל אביב'},
            {'שם': 'أحمد علي', 'טלפון': '054-111-2222', 'אימייל': 'ahmad@test.org', 'עיר': 'الناصرة'},  # Arabic
            {'שם': 'Владимир Петров', 'טלפון': '053-333-4444', 'אימייל': 'vladimir@test.ru', 'עיר': 'עיר רוסית'},  # Russian
            {'שם': '张伟', 'טלפון': '050-555-6666', 'אימייל': 'zhang@test.cn', 'עיר': 'עיר סינית'},  # Chinese
        ]
        
        # Test with different encodings
        for encoding in ['utf-8-sig', 'utf-8', 'cp1255']:
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding=encoding)
            df = pd.DataFrame(encoding_test_data)
            try:
                df.to_csv(temp_file.name, index=False, encoding=encoding)
                temp_file.close()
                
                output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
                
                # Should handle the encoding gracefully
                extraction.clean_csv_data(temp_file.name, output_file, use_openai=False)
                
                # Verify output is readable
                result_df = pd.read_csv(output_file, encoding='utf-8-sig')
                assert len(result_df) > 0, f"Should process {encoding} encoded file"
                
                # Hebrew should be preserved
                hebrew_found = any(any(c in str(name) for c in 'אבגדהוזחטיכלמנסעפצקרשת') 
                                 for name in result_df['שם'].tolist())
                assert hebrew_found, f"Hebrew should be preserved from {encoding} file"
                
                os.unlink(output_file)
                
            except UnicodeEncodeError:
                # Some encodings might not support all characters - that's OK
                temp_file.close()
            finally:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

    def test_memory_usage_with_duplicates(self):
        """Test memory efficiency when processing datasets with many duplicates."""
        
        # Create dataset with many duplicates
        base_contact = {
            'שם': 'דוד כהן',
            'טלפון': '052-123-4567',
            'אימייל': 'david@test.com',
            'מחלקה': 'מחלקת חינוך',
            'עיר': 'תל אביב'
        }
        
        # Create 500 identical contacts (should be deduplicated to 1)
        duplicate_dataset = [base_contact.copy() for _ in range(500)]
        
        # Add a few unique contacts
        for i in range(5):
            unique_contact = base_contact.copy()
            unique_contact['שם'] = f'איש {i}'
            unique_contact['טלפון'] = f'052-{i:03d}-7890'
            unique_contact['אימייל'] = f'person{i}@test.com'
            duplicate_dataset.append(unique_contact)
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig')
        df = pd.DataFrame(duplicate_dataset)
        df.to_csv(temp_file.name, index=False, encoding='utf-8-sig')
        temp_file.close()
        
        output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
        
        try:
            # Process the duplicates
            extraction.clean_csv_data(temp_file.name, output_file, use_openai=False)
            
            result_df = pd.read_csv(output_file, encoding='utf-8-sig')
            
            # Should dramatically reduce the dataset size
            assert len(result_df) <= 10, f"Should deduplicate to ~6 contacts, got {len(result_df)}"
            
            # Verify no duplicate phone numbers
            phones = result_df['טלפון'].dropna()
            assert phones.nunique() == len(phones), "Should have no duplicate phone numbers"
            
        finally:
            os.unlink(temp_file.name)
            os.unlink(output_file)

    def test_contact_extraction_edge_cases(self):
        """Test Contact object creation with various edge cases."""
        
        edge_cases = [
            # Empty text
            ("", "עיר"),
            
            # Only whitespace
            ("   \n\t   ", "עיר"),
            
            # Only punctuation
            ("!@#$%^&*()", "עיר"),
            
            # Very long text
            ("א" * 10000, "עיר"),
            
            # Mixed scripts
            ("David דוד Cohen כהן Ahmad أحمد", "עיר"),
            
            # Only numbers
            ("123456789", "עיר"),
            
            # HTML/XML tags
            ("<div>דוד כהן</div> <email>david@test.com</email>", "עיר"),
            
            # Multiple emails and phones
            ("דוד כהן david@test.com rachel@test.com 052-123-4567 054-111-2222", "עיר"),
        ]
        
        for text, city in edge_cases:
            try:
                contact = Contacts(text, city)
                
                # Should not crash
                assert contact.city == city
                assert hasattr(contact, 'name')
                assert hasattr(contact, 'email')
                assert hasattr(contact, 'phone_mobile')
                assert hasattr(contact, 'phone_office')
                
                # Name should be either valid or "לא נמצא שם"
                if contact.name:
                    assert isinstance(contact.name, str)
                    assert len(contact.name) > 0
                
            except Exception as e:
                pytest.fail(f"Contact creation failed for text '{text[:50]}...': {e}")

    def test_batch_processing_efficiency(self, monkeypatch):
        """Test the efficiency of batch processing in OpenAI integration."""
        
        # Mock OpenAI processing to simulate realistic timing
        call_count = 0
        def mock_gpt_fix(name, dept):
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Simulate API delay
            return name, dept
        
        monkeypatch.setattr(extraction, "gpt_fix_names_and_department", mock_gpt_fix)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        # Create test data
        test_data = []
        for i in range(50):  # 50 contacts
            test_data.append({
                'שם': f'David {i}',
                'טלפון': f'052-{i:03d}-1234',
                'אימייל': f'david{i}@test.com',
                'מחלקה': 'education',
                'עיר': f'עיר {i%5}'
            })
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig')
        df = pd.DataFrame(test_data)
        df.to_csv(temp_file.name, index=False, encoding='utf-8-sig')
        temp_file.close()
        
        output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
        
        try:
            start_time = time.time()
            extraction.clean_csv_data(temp_file.name, output_file, use_openai=True)
            processing_time = time.time() - start_time
            
            # Should process in reasonable time with batching
            assert processing_time < 10, f"Batch processing took too long: {processing_time:.2f}s"
            
            # Should have called OpenAI for each contact
            assert call_count == 50, f"Expected 50 OpenAI calls, got {call_count}"
            
            # Verify output
            result_df = pd.read_csv(output_file, encoding='utf-8-sig')
            assert len(result_df) == 50, "Should preserve all contacts"
            
        finally:
            os.unlink(temp_file.name)
            os.unlink(output_file)

    def test_concurrent_processing_safety(self):
        """Test that the processing is safe for concurrent operations."""
        
        # This test ensures that temporary files and processing don't interfere
        import threading
        import queue
        
        results = queue.Queue()
        
        def process_dataset(dataset_id):
            try:
                test_data = [
                    {'שם': f'איש {dataset_id}', 'טלפון': f'052-{dataset_id:03d}-1234', 
                     'אימייל': f'person{dataset_id}@test.com', 'עיר': f'עיר {dataset_id}'}
                ]
                
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'_{dataset_id}.csv', 
                                                     delete=False, encoding='utf-8-sig')
                df = pd.DataFrame(test_data)
                df.to_csv(temp_file.name, index=False, encoding='utf-8-sig')
                temp_file.close()
                
                output_file = tempfile.NamedTemporaryFile(suffix=f'_out_{dataset_id}.csv', delete=False).name
                
                extraction.clean_csv_data(temp_file.name, output_file, use_openai=False)
                
                result_df = pd.read_csv(output_file, encoding='utf-8-sig')
                results.put((dataset_id, len(result_df), True))
                
                os.unlink(temp_file.name)
                os.unlink(output_file)
                
            except Exception as e:
                results.put((dataset_id, 0, False))
        
        # Run multiple threads concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_dataset, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            dataset_id, row_count, success = results.get()
            if success:
                success_count += 1
                assert row_count == 1, f"Dataset {dataset_id} should have 1 row"
        
        assert success_count == 5, f"All 5 concurrent processes should succeed, got {success_count}"
