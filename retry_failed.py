#!/usr/bin/env python3

import json
import os
from download_from_list import download_speech, create_speech_dir
from login_script import main as login
from tqdm import tqdm

def main():
    # Load progress and report files
    try:
        with open('download_progress.json') as f:
            progress = json.load(f)
        with open('speeches_list.json') as f:
            data = json.load(f)
            speeches = {s['speech_id']: s for s in data['speeches']}
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
        return

    failed_ids = progress.get('failed', [])
    if not failed_ids:
        print("No failed downloads found in download_progress.json")
        return

    print(f"\nFound {len(failed_ids)} failed downloads to retry")
    
    # Get failed speeches
    to_retry = [speeches[speech_id] for speech_id in failed_ids if speech_id in speeches]
    
    if not to_retry:
        print("No matching speeches found for failed IDs")
        return

    print("\nLogging in to OtterAI...")
    otter = login()

    print("\nRetrying failed downloads:")
    
    # Track new results
    new_results = {'succeeded': [], 'failed': []}
    
    with tqdm(total=len(to_retry), desc="Retrying") as pbar:
        for speech in to_retry:
            speech_id = speech['speech_id']
            
            # Create fresh directory for retry
            directory = create_speech_dir(speech)
            pbar.set_description(f"Retrying {speech_id}")
            
            if download_speech(otter, speech, directory):
                new_results['succeeded'].append(speech_id)
                # Remove from failed list if successful
                if speech_id in progress['failed']:
                    progress['failed'].remove(speech_id)
                progress['downloaded'].append(speech_id)
            else:
                new_results['failed'].append(speech_id)
                
            # Update progress file after each attempt
            with open('download_progress.json', 'w') as f:
                json.dump(progress, f, indent=2)
                
            pbar.set_postfix(success=len(new_results['succeeded']), 
                           still_failed=len(new_results['failed']))
            pbar.update(1)
    
    print("\nRetry complete!")
    print(f"Successfully downloaded: {len(new_results['succeeded'])}")
    print(f"Still failed: {len(new_results['failed'])}")
    
    if new_results['failed']:
        print("\nSpeeches that still failed:")
        for speech_id in new_results['failed']:
            print(f"- {speech_id}: {speeches[speech_id]['title']}")

if __name__ == "__main__":
    main()
