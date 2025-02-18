#!/usr/bin/env python3

import os
import json
from datetime import datetime
from tabulate import tabulate

def check_download_integrity(directory, speech_id):
    """Check if a downloaded speech has all expected files"""
    required_files = {
        'metadata.json': False,
        f'{speech_id}.zip': False
    }
    
    try:
        for filename in os.listdir(directory):
            for req_file in required_files:
                if filename.endswith(req_file):
                    required_files[req_file] = True
                    file_size = os.path.getsize(os.path.join(directory, filename))
                    if file_size == 0:
                        print(f"Warning: {filename} is empty (0 bytes)")
                        required_files[req_file] = False
                        
        return all(required_files.values())
    except Exception as e:
        print(f"Error checking directory {directory}: {e}")
        return False

def main():
    # Load progress data
    try:
        with open('download_progress.json') as f:
            progress = json.load(f)
        with open('speeches_list.json') as f:
            data = json.load(f)
            speeches = {s['speech_id']: s for s in data['speeches']}
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
        return

    print("\nValidating downloads...")
    
    # Track validation results
    validation = {
        'verified': [],
        'missing_files': [],
        'not_found': [],
        'empty_files': []
    }

    # Check all supposedly downloaded speeches
    downloaded_ids = progress.get('downloaded', [])
    failed_ids = progress.get('failed', [])
    
    # Build table of results
    results = []
    
    for speech_id in downloaded_ids:
        speech = speeches.get(speech_id, {})
        title = speech.get('title', 'Unknown')
        date = datetime.fromtimestamp(speech.get('created_at', 0)).strftime('%Y-%m-%d')
        
        # Look for speech directory
        found = False
        for root, dirs, files in os.walk('downloads'):
            if speech_id in root:
                found = True
                if check_download_integrity(root, speech_id):
                    validation['verified'].append(speech_id)
                    status = "✓ Verified"
                else:
                    validation['missing_files'].append(speech_id)
                    status = "✗ Missing files"
                break
                
        if not found:
            validation['not_found'].append(speech_id)
            status = "✗ Directory not found"
            
        results.append([speech_id, title, date, status])

    # Print summary table
    print("\nDownload Status:")
    print(tabulate(results, 
                  headers=['Speech ID', 'Title', 'Date', 'Status'],
                  tablefmt='grid'))
    
    # Print summary
    print("\nSummary:")
    print(f"Total speeches: {len(speeches)}")
    print(f"Marked as downloaded: {len(downloaded_ids)}")
    print(f"Marked as failed: {len(failed_ids)}")
    print(f"Verified complete: {len(validation['verified'])}")
    print(f"Missing files: {len(validation['missing_files'])}")
    print(f"Not found: {len(validation['not_found'])}")
    
    # Look at remaining failed download
    print("\nExamining failed downloads:")
    for speech_id in failed_ids:
        speech = speeches.get(speech_id, {})
        print(f"\nFailed Speech Details:")
        print(f"ID: {speech_id}")
        print(f"Title: {speech.get('title')}")
        print(f"Created: {datetime.fromtimestamp(speech.get('created_at', 0))}")
        print(f"OTID: {speech.get('otid')}")
        print(f"Download URL: {speech.get('download_url')}")
        
    # Save validation report
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'validation_results': validation,
        'failed_details': [speeches[id] for id in failed_ids if id in speeches]
    }
    
    with open('validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\nDetailed validation report saved to validation_report.json")

if __name__ == "__main__":
    main()
