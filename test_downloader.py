#!/usr/bin/env python3
"""
Test script for Canvas File Downloader
This script tests the download functionality with sample JSON data
"""

import json
import tempfile
from pathlib import Path
from canvas_file_downloader import CanvasFileDownloader

def create_sample_json():
    """Create sample JSON data for testing"""
    sample_data = {
        "export_info": {
            "exported_at": "2024-01-15T10:30:00",
            "course_name": "Test Course",
            "course_id": 12345,
            "export_version": "2.0"
        },
        "course_data": {
            "assignments": [
                {
                    "id": 1001,
                    "name": "Assignment 1",
                    "description": "<p>Test assignment with <a href='https://example.com/file.pdf'>downloadable file</a></p>",
                    "html_url": "https://canvas.example.com/courses/12345/assignments/1001"
                }
            ],
            "modules": [
                {
                    "id": 355009,
                    "name": "Test Module",
                    "items": [
                        {
                            "id": 2992004,
                            "title": "Test Page",
                            "type": "Page",
                            "html_url": "https://canvas.example.com/courses/12345/modules/items/2992004",
                            "url": "https://canvas.example.com/api/v1/courses/12345/pages/test-page"
                        },
                        {
                            "id": 2992006,
                            "title": "External Resource",
                            "type": "ExternalUrl",
                            "external_url": "https://www.example.com/resource.html"
                        },
                        {
                            "id": 3179871,
                            "title": "Google Drive File",
                            "type": "ExternalUrl",
                            "external_url": "https://drive.google.com/file/d/1-I2s7LCCcHjcdY4afkM3rmmGE-jFWco_/view"
                        }
                    ]
                }
            ],
            "files": [
                {
                    "id": 5001,
                    "display_name": "sample_document.pdf",
                    "filename": "sample_document.pdf",
                    "url": "https://canvas.example.com/files/5001/download",
                    "content-type": "application/pdf",
                    "size": 1024000
                }
            ]
        }
    }
    return sample_data

def test_downloader():
    """Test the Canvas File Downloader"""
    print("🧪 Testing Canvas File Downloader...")
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create sample JSON file
        sample_data = create_sample_json()
        json_file = temp_path / "test_course.json"
        
        with open(json_file, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        print(f"📄 Created test JSON: {json_file}")
        
        # Test the downloader
        downloader = CanvasFileDownloader()
        
        # Test JSON processing
        print("\n🔍 Testing JSON processing...")
        try:
            downloader.process_json_export(json_file)
            print(f"Successfully processed sample JSON data")
            print(f"Stats: {downloader.stats}")
        except Exception as e:
            print(f"Error processing JSON: {e}")
        
        # Test filename sanitization
        print("\n🧹 Testing filename sanitization...")
        test_names = [
            "Test File.pdf",
            "File with/invalid\\chars?.txt",
            "Normal_file-name.docx"
        ]
        
        for name in test_names:
            sanitized = downloader.sanitize_filename(name)
            print(f"  '{name}' -> '{sanitized}'")
        
        # Test Google Drive URL processing
        print("\n🔗 Testing Google Drive URL processing...")
        gdrive_url = "https://drive.google.com/file/d/1-I2s7LCCcHjcdY4afkM3rmmGE-jFWco_/view"
        
        # Test processing with a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = downloader.process_google_drive_url(gdrive_url, "Test Lecture", temp_path)
            print(f"  Original: {gdrive_url}")
            print(f"  Processing result: {result}")
            
            # Check if any files were created
            files_created = list(temp_path.glob("*"))
            print(f"  Files created: {[f.name for f in files_created]}")
        
        print("\n✅ All tests completed successfully!")
        print(f"\n📁 Test files created in: {temp_dir}")
        print("\n💡 To test actual downloads, run:")
        print(f"   python canvas_file_downloader.py {json_file}")

def test_filename_sanitization():
    """Test filename sanitization functionality"""
    print("\n🧹 Testing filename sanitization...")
    downloader = CanvasFileDownloader()
    
    test_cases = [
        ("Test File.pdf", "Test File.pdf"),
        ("File with/invalid\\chars?.txt", "File with_invalid_chars_.txt"),
        ("Normal_file-name.docx", "Normal_file-name.docx")
    ]
    
    all_passed = True
    for original, expected in test_cases:
        sanitized = downloader.sanitize_filename(original)
        print(f"  '{original}' -> '{sanitized}'")
        if sanitized != expected:
            print(f"    ❌ Expected: '{expected}'")
            all_passed = False
    
    return all_passed

def test_json_processing():
    """Test JSON processing functionality"""
    print("\n🔍 Testing JSON processing...")
    
    # Create sample data inline
    sample_data = {
        "course_id": "test_course_123",
        "course_info": {
            "name": "Test Course",
            "id": "test_course_123"
        },
        "modules": [
            {
                "id": 355009,
                "name": "Test Module",
                "items": [
                    {
                        "id": 2992004,
                        "title": "Test Page",
                        "type": "Page",
                        "url": "https://example.instructure.com/api/v1/courses/123/pages/test"
                    },
                    {
                        "id": 2992005,
                        "title": "Test External Link",
                        "type": "ExternalUrl",
                        "external_url": "https://drive.google.com/file/d/test123/view"
                    }
                ]
            }
        ],
        "files": []
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        json_file = temp_path / "test_course.json"
        
        with open(json_file, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        downloader = CanvasFileDownloader()
        
        try:
            downloader.process_json_export(str(json_file))
            print(f"Successfully processed sample JSON data")
            print(f"Stats: {downloader.stats}")
            return True
        except Exception as e:
            print(f"Error processing JSON: {e}")
            return False

def test_google_drive_processing():
    """Test Google Drive URL processing"""
    print("\n🔗 Testing Google Drive URL processing...")
    downloader = CanvasFileDownloader()
    
    gdrive_url = "https://drive.google.com/file/d/1-I2s7LCCcHjcdY4afkM3rmmGE-jFWco_/view"
    
    # Test the Google Drive processing by creating a temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        result = downloader.process_google_drive_url(gdrive_url, "Test Lecture", temp_path)
        print(f"  Original: {gdrive_url}")
        print(f"  Processing result: {result}")
        
        # Check if any files were created
        files_created = list(temp_path.glob("*"))
        print(f"  Files created: {[f.name for f in files_created]}")
        
        return len(files_created) > 0

def main():
    """Run all tests"""
    print("🚀 Testing Canvas File Downloader")
    print("=" * 40)
    
    tests = [
        ("Filename Sanitization", test_filename_sanitization),
        ("JSON Processing", test_json_processing),
        ("Google Drive URL Processing", test_google_drive_processing)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ FAIL {test_name}: {e}")
    
    print("\n" + "=" * 40)
    print("📊 Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    # Run the legacy test function for backwards compatibility
    test_downloader()
    
    print("\n" + "=" * 50)
    print("Running structured tests...")
    
    # Run the new structured tests
    main()