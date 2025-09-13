#!/usr/bin/env python3
"""
Canvas File Downloader

A standalone script to download files from Canvas course JSON exports.
Supports Canvas API URLs, external URLs, and direct file downloads.
"""

import argparse
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, unquote, parse_qs
from datetime import datetime

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('canvas_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CanvasFileDownloader:
    """Download files from Canvas course JSON exports"""
    
    def __init__(self, api_token: str = None, base_url: str = None, output_dir: str = "downloads", dry_run: bool = False):
        """
        Initialize the downloader
        
        Args:
            api_token: Canvas API token (optional, for authenticated requests)
            base_url: Canvas base URL (optional)
            output_dir: Directory to save downloaded files
            dry_run: If True, only show what would be downloaded without downloading
        """
        self.api_token = api_token
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        self.session = requests.Session()
        
        # Set up session headers if token provided
        if self.api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'User-Agent': 'Canvas-File-Downloader/1.0'
            })
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'downloaded': 0,
            'skipped': 0,
            'errors': 0,
            'external_urls': 0
        }
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        return filename or 'unnamed_file'
    
    def get_filename_from_url(self, url: str, default_name: str = None) -> str:
        """Extract filename from URL"""
        try:
            parsed = urlparse(url)
            filename = os.path.basename(unquote(parsed.path))
            if filename and '.' in filename:
                return self.sanitize_filename(filename)
        except Exception:
            pass
        
        return self.sanitize_filename(default_name or 'downloaded_file')
    
    def download_file(self, url: str, filename: str, course_dir: Path) -> bool:
        """Download a single file with improved error handling
        
        Args:
            url: URL to download from
            filename: Suggested filename
            course_dir: Directory to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create course directory if it doesn't exist
            course_dir.mkdir(parents=True, exist_ok=True)
            
            # Get filename from URL if not provided
            if not filename or filename == 'unknown_file':
                filename = self.get_filename_from_url(url)
            
            # Sanitize filename
            safe_filename = self.sanitize_filename(filename)
            filepath = course_dir / safe_filename
            
            # Skip if file already exists
            if filepath.exists():
                logger.info(f"File already exists, skipping: {safe_filename}")
                self.stats['skipped'] += 1
                return True
            
            logger.info(f"{'[DRY RUN] Would download' if self.dry_run else 'Downloading'}: {safe_filename} from {url}")
            
            # In dry-run mode, just simulate the download
            if self.dry_run:
                logger.info(f"[DRY RUN] Would save to: {filepath}")
                self.stats['downloaded'] += 1
                return True
            
            # Download with timeout and streaming
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = self.session.get(url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()
            
            # Check content type for potential issues
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type and not filename.endswith('.html'):
                logger.warning(f"Received HTML content for {filename}, might be an error page")
            
            # Write file in chunks with verification
            temp_filepath = filepath.with_suffix(filepath.suffix + '.tmp')
            total_size = 0
            
            with open(temp_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            # Verify download completed successfully
            if total_size == 0:
                logger.error(f"Downloaded file is empty: {safe_filename}")
                temp_filepath.unlink()
                self.stats['errors'] += 1
                return False
            
            # Move temp file to final location
            temp_filepath.rename(filepath)
            
            logger.info(f"Downloaded: {safe_filename} ({total_size} bytes)")
            self.stats['downloaded'] += 1
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error downloading {filename}: {e}")
            self.stats['errors'] += 1
            return False
        except Exception as e:
            logger.error(f"Error downloading {filename}: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_canvas_page_url(self, url: str, title: str, course_dir: Path) -> bool:
        """Process Canvas page URL and save content"""
        try:
            if not self.api_token:
                logger.warning(f"No API token provided, skipping Canvas page: {title}")
                return False
            
            logger.info(f"Fetching Canvas page: {title}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            page_data = response.json()
            content = page_data.get('body', '')
            
            if content:
                safe_filename = self.sanitize_filename(f"{title}.html")
                filepath = course_dir / safe_filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"<html><head><title>{title}</title></head><body>")
                    f.write(content)
                    f.write("</body></html>")
                
                logger.info(f"Saved Canvas page: {safe_filename}")
                self.stats['downloaded'] += 1
                return True
            
        except Exception as e:
            logger.error(f"Error processing Canvas page {title}: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_external_url(self, url: str, title: str, course_dir: Path) -> bool:
        """Process external URL (save link info)"""
        try:
            # For external URLs, save a link file
            safe_filename = self.sanitize_filename(f"{title}_link.txt")
            filepath = course_dir / safe_filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Saved: {datetime.now().isoformat()}\n")
            
            logger.info(f"Saved external link: {safe_filename}")
            self.stats['external_urls'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error saving external URL {title}: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_google_drive_url(self, url: str, title: str, course_dir: Path) -> bool:
        """Process Google Drive URL and attempt direct download"""
        try:
            # Convert Google Drive view URL to download URL
            if '/file/d/' in url and '/view' in url:
                file_id = url.split('/file/d/')[1].split('/')[0]
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                
                logger.info(f"Converting Google Drive URL for: {title}")
                return self.download_file(download_url, f"{title}.pdf", course_dir)
            else:
                # Save as link if can't convert
                return self.process_external_url(url, title, course_dir)
                
        except Exception as e:
            logger.error(f"Error processing Google Drive URL {title}: {e}")
            return self.process_external_url(url, title, course_dir)
    
    def process_module_items(self, items: List[Dict], course_dir: Path) -> None:
        """Process module items and download content"""
        for item in items:
            self.stats['total_files'] += 1
            
            title = item.get('title', 'Untitled')
            item_type = item.get('type', 'Unknown')
            
            # Process different types of URLs
            if 'url' in item and item['url']:
                url = item['url']
                
                if 'pages' in url:
                    # Canvas page
                    self.process_canvas_page_url(url, title, course_dir)
                elif item_type == 'File' or 'files' in url:
                    # Canvas file
                    filename = item.get('display_name', title)
                    self.download_file(url, filename, course_dir)
                else:
                    # Other Canvas API content
                    self.process_canvas_page_url(url, title, course_dir)
            
            elif 'external_url' in item and item['external_url']:
                url = item['external_url']
                
                if 'drive.google.com' in url:
                    # Google Drive file
                    self.process_google_drive_url(url, title, course_dir)
                else:
                    # Other external URL
                    self.process_external_url(url, title, course_dir)
            
            elif 'html_url' in item and item['html_url']:
                # HTML URL (usually for viewing)
                self.process_external_url(item['html_url'], title, course_dir)
    
    def process_course_files(self, files: List[Dict], course_dir: Path) -> None:
        """Process course files list"""
        files_dir = course_dir / "course_files"
        
        for file_info in files:
            self.stats['total_files'] += 1
            
            filename = file_info.get('display_name', file_info.get('filename', 'unknown_file'))
            file_url = file_info.get('url')
            
            if file_url:
                self.download_file(file_url, filename, files_dir)
    
    def process_json_export(self, json_file: str) -> None:
        """Process a single JSON export file"""
        try:
            logger.info(f"Processing JSON export: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                course_data = json.load(f)
            
            # Get course info
            course_info = course_data.get('course_info', {})
            course_name = course_info.get('name', f"Course_{course_data.get('course_id', 'Unknown')}")
            course_id = course_data.get('course_id', 'unknown')
            
            # Create course directory
            safe_course_name = self.sanitize_filename(course_name)
            course_dir = self.output_dir / f"course_{course_id}_{safe_course_name}"
            
            logger.info(f"Processing course: {course_name} (ID: {course_id})")
            
            # Process modules and their items
            modules = course_data.get('modules', [])
            for module in modules:
                module_name = module.get('name', 'Unnamed Module')
                logger.info(f"Processing module: {module_name}")
                
                items = module.get('items', [])
                if items:
                    module_dir = course_dir / self.sanitize_filename(module_name)
                    self.process_module_items(items, module_dir)
            
            # Process course files
            files = course_data.get('files', [])
            if files:
                logger.info(f"Processing {len(files)} course files")
                self.process_course_files(files, course_dir)
            
            logger.info(f"Completed processing: {course_name}")
            
        except Exception as e:
            logger.error(f"Error processing JSON file {json_file}: {e}")
            self.stats['errors'] += 1
    
    def download_from_json_files(self, json_files: List[str]) -> None:
        """Download files from multiple JSON export files"""
        logger.info(f"Starting download process for {len(json_files)} JSON files")
        start_time = time.time()
        
        for json_file in json_files:
            if os.path.exists(json_file):
                self.process_json_export(json_file)
            else:
                logger.error(f"JSON file not found: {json_file}")
                self.stats['errors'] += 1
        
        # Print statistics
        elapsed_time = time.time() - start_time
        logger.info("\n" + "="*50)
        logger.info("DOWNLOAD STATISTICS")
        logger.info("="*50)
        logger.info(f"Total items processed: {self.stats['total_files']}")
        logger.info(f"Files downloaded: {self.stats['downloaded']}")
        logger.info(f"Files skipped (already exist): {self.stats['skipped']}")
        logger.info(f"External URLs saved: {self.stats['external_urls']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        logger.info(f"Total time: {elapsed_time:.2f} seconds")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
        logger.info("="*50)

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Download files from Canvas JSON exports')
    parser.add_argument('json_files', nargs='*', help='JSON export files to process (if not specified, will look for all JSON files)')
    parser.add_argument('--output-dir', '-o', default='downloads', help='Output directory for downloads')
    parser.add_argument('--api-token', '-t', help='Canvas API token for authenticated requests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be downloaded without downloading')
    parser.add_argument('--course', '-c', help='Download specific course by name (partial match)')
    parser.add_argument('--all-courses', '-a', action='store_true', help='Download from all JSON files in current directory')
    parser.add_argument('--list-courses', '-l', action='store_true', help='List available courses in JSON files')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Determine which JSON files to process
    json_files = []
    
    if args.all_courses:
        # Find all JSON files in current directory
        import glob
        json_files = glob.glob('*.json')
        if not json_files:
            logger.error("No JSON files found in current directory")
            return
        logger.info(f"Found {len(json_files)} JSON files: {', '.join(json_files)}")
    elif args.json_files:
        json_files = args.json_files
    else:
        # Interactive mode - let user choose
        import glob
        available_files = glob.glob('*.json')
        if not available_files:
            logger.error("No JSON files found. Please specify JSON files or use --all-courses")
            return
        
        print("\nAvailable JSON files:")
        for i, file in enumerate(available_files, 1):
            print(f"{i}. {file}")
        
        choice = input("\nEnter file numbers (comma-separated) or 'all' for all files: ").strip()
        if choice.lower() == 'all':
            json_files = available_files
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                json_files = [available_files[i] for i in indices if 0 <= i < len(available_files)]
            except (ValueError, IndexError):
                logger.error("Invalid selection")
                return
    
    if not json_files:
        logger.error("No JSON files to process")
        return
    
    # List courses mode
    if args.list_courses:
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                course_name = data.get('course', {}).get('name', 'Unknown Course')
                course_id = data.get('course', {}).get('id', 'Unknown ID')
                print(f"{json_file}: {course_name} (ID: {course_id})")
            except Exception as e:
                print(f"{json_file}: Error reading file - {e}")
        return
    
    # Filter by course name if specified
    if args.course:
        filtered_files = []
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                course_name = data.get('course', {}).get('name', '').lower()
                if args.course.lower() in course_name:
                    filtered_files.append(json_file)
                    logger.info(f"Selected course: {data.get('course', {}).get('name', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")
        
        if not filtered_files:
            logger.error(f"No courses found matching '{args.course}'")
            return
        
        json_files = filtered_files
    
    # Initialize downloader
    downloader = CanvasFileDownloader(api_token=args.api_token, output_dir=args.output_dir, dry_run=args.dry_run)
    
    # Process each JSON file
    for json_file in json_files:
        logger.info(f"Processing: {json_file}")
        downloader.download_from_json_files([json_file])
    
    # Print final statistics
    logger.info(f"Download complete. Downloaded: {downloader.stats['downloaded']}, "
                f"Skipped: {downloader.stats['skipped']}, Errors: {downloader.stats['errors']}")

if __name__ == '__main__':
    main()