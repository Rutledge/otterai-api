#!/usr/bin/env python3

import json
import os
from datetime import datetime
from tabulate import tabulate

def main():
    # Load progress file
    try:
        with open('download_progress.json') as f:
            progress = json.load(f)
    except FileNotFoundError:
        print("Error: download_progress.json not found!")
        print("Please run the download script first")
        return
        
    # Load original speeches list for metadata
    try:
        with open('speeches_list.json') as f:
            data = json.load(f)
            speeches = {s['speech_id']: s for s in data.get('speeches', [])}
    except FileNotFoundError:
        print("Error: speeches_list.json not found!")
        print("Please run list_all_speeches.py first")
        return

    failed = progress.get('failed', [])
    if not failed:
        print("\nNo failed downloads found!")
        return
        
    print(f"\nFound {len(failed)} failed downloads:")
    
    # Collect info about failed downloads
    failed_info = []
    for speech_id in failed:
        speech = speeches.get(speech_id, {})
        failed_info.append([
            speech_id,
            speech.get('title', 'Unknown'),
            datetime.fromtimestamp(speech.get('created_at', 0)).strftime('%Y-%m-%d'),
            speech.get('otid', 'Unknown')
        ])
    
    # Print table of failed downloads
    print("\nFailed Downloads:")
    print(tabulate(
        failed_info,
        headers=['Speech ID', 'Title', 'Created', 'OTID'],
        tablefmt='grid'
    ))
    
    # Save detailed report
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_speeches': len(speeches),
        'downloaded': len(progress.get('downloaded', [])),
        'failed': len(failed),
        'failed_details': [
            {
                'speech_id': speech_id,
                'title': speeches.get(speech_id, {}).get('title', 'Unknown'),
                'created_at': speeches.get(speech_id, {}).get('created_at', 0),
                'otid': speeches.get(speech_id, {}).get('otid', 'Unknown')
            }
            for speech_id in failed
        ]
    }
    
    with open('download_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to download_report.json")
    print("\nTo retry failed downloads:")
    print("1. Remove failed IDs from download_progress.json")
    print("2. Run download_from_list.py again")

if __name__ == "__main__":
    main()
