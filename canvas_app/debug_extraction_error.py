#!/usr/bin/env python3
"""
Debug script to identify why text extraction is failing in the Canvas app
"""

import sys
import os
from pathlib import Path

# Add navdeep to path
navdeep_src_path = "/Users/praveenbhandari/sf-vibe/navdeep/src"
if navdeep_src_path not in sys.path:
    sys.path.insert(0, navdeep_src_path)

from pipelines.text_extraction_pipeline import TextExtractionPipeline

def debug_extraction_issue():
    """Debug the text extraction issue"""
    print("🔍 Debugging Text Extraction Issue")
    print("=" * 50)
    
    # Initialize pipeline
    try:
        pipeline = TextExtractionPipeline()
        print("✅ Pipeline initialized successfully")
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        return
    
    # Check downloads directory for actual files
    downloads_dir = Path("/Users/praveenbhandari/sf-vibe/downloads")
    print(f"\n📁 Checking downloads directory: {downloads_dir}")
    
    if not downloads_dir.exists():
        print("❌ Downloads directory does not exist")
        return
    
    # Find PDF files to test with
    pdf_files = list(downloads_dir.rglob("*.pdf"))
    txt_files = list(downloads_dir.rglob("*.txt"))
    doc_files = list(downloads_dir.rglob("*.doc*"))
    
    print(f"Found {len(pdf_files)} PDF files")
    print(f"Found {len(txt_files)} TXT files")
    print(f"Found {len(doc_files)} DOC files")
    
    # Test with the first available file
    test_files = pdf_files + txt_files + doc_files
    
    if not test_files:
        print("❌ No supported files found in downloads directory")
        # Create a test file
        test_file = downloads_dir / "debug_test.txt"
        test_file.write_text("This is a test file for debugging text extraction.")
        test_files = [test_file]
        print(f"✅ Created test file: {test_file}")
    
    # Test extraction with first file
    test_file = test_files[0]
    print(f"\n🧪 Testing extraction with: {test_file}")
    print(f"   File exists: {test_file.exists()}")
    print(f"   File size: {test_file.stat().st_size if test_file.exists() else 'N/A'} bytes")
    
    try:
        result = pipeline.extract_from_file(str(test_file))
        print(f"\n📊 Extraction Result:")
        print(f"   Type: {type(result)}")
        print(f"   Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            print(f"   Success: {result.get('success')}")
            print(f"   Error: {result.get('error')}")
            print(f"   Text length: {len(result.get('text', '')) if result.get('text') else 0}")
            
            if result.get('text'):
                preview = result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
                print(f"   Text preview: {repr(preview)}")
            
            if result.get('metadata'):
                print(f"   Metadata: {result['metadata']}")
                
            # Check the specific condition from Canvas app
            if result.get('success') and result.get('text'):
                print("✅ Extraction would succeed in Canvas app")
            else:
                print("❌ Extraction would fail in Canvas app")
                print(f"   Reason: success={result.get('success')}, text_exists={bool(result.get('text'))}")
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            print(f"   Result: {result}")
            
    except Exception as e:
        print(f"❌ Extraction failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with different file types
    print("\n🔄 Testing different file types:")
    
    # Test TXT extraction specifically
    test_txt = downloads_dir / "debug_test.txt"
    if not test_txt.exists():
        test_txt.write_text("This is a test TXT file for debugging.\nIt has multiple lines.\nAnd some content.")
    
    print(f"\n📄 Testing TXT file: {test_txt}")
    try:
        result = pipeline.extract_from_file(str(test_txt))
        print(f"   Success: {result.get('success') if isinstance(result, dict) else 'N/A'}")
        print(f"   Text length: {len(result.get('text', '')) if isinstance(result, dict) and result.get('text') else 0}")
        if isinstance(result, dict) and result.get('error'):
            print(f"   Error: {result['error']}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Check supported formats
    print("\n📋 Supported formats:")
    try:
        formats = pipeline.get_supported_formats()
        for fmt, extractor in formats.items():
            print(f"   {fmt}: {extractor.__class__.__name__}")
    except Exception as e:
        print(f"   Error getting formats: {e}")

if __name__ == "__main__":
    debug_extraction_issue()