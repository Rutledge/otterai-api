#!/usr/bin/env python3

import os
import sys
import json
import requests
from datetime import datetime
from tqdm import tqdm  # Add this import
from login_script import main as login

def create_speech_directory(speech, base_dir="downloads"):
    """Create a directory for each speech using title and date"""
    created_at = datetime.fromtimestamp(speech.get('created_at', 0))
    date_str = created_at.strftime('%Y%m%d')
    
    # Clean title for filesystem and add speech_id to make unique
    title = speech.get('title', 'Untitled').replace('/', '_').replace('\\', '_')
    speech_id = speech.get('speech_id', '')[:8]  # Use first 8 chars of ID
    dir_name = f"{date_str}_{title}_{speech_id}"[:100]  # Limit length
    
    full_path = os.path.join(base_dir, dir_name)
    os.makedirs(full_path, exist_ok=True)
    
    return full_path

def download_speech_content(otter, speech, output_dir):
    """Download all content for a speech"""
    speech_id = speech.get('speech_id')
    speech_otid = speech.get('speech_otid', speech.get('otid'))
    
    print(f"\nProcessing: {speech.get('title')}")
    print(f"Directory: {output_dir}")
    print(f"IDs: speech_id={speech_id}, otid={speech_otid}")
    
    try:
        # Save metadata
        metadata_file = os.path.join(output_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(speech, f, indent=2)
        print(f"✓ Saved metadata to {metadata_file}")
        
        # Download content
        try:
            zip_path = os.path.join(output_dir, "content")
            print(f"Downloading to: {zip_path}")
            otter.download_speech(speech_otid, name=zip_path, fileformat="txt,pdf,mp3,docx,srt")
            
            # Verify files were created
            zip_file = f"{zip_path}.zip"
            if os.path.exists(zip_file):
                print(f"✓ Downloaded content to {zip_file} ({os.path.getsize(zip_file)} bytes)")
            else:
                print(f"✗ Failed to find downloaded file at {zip_file}")
            
        except Exception as e:
            print(f"✗ Download failed: {e}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def load_download_tracker(base_dir):
    """Load the download tracker file"""
    tracker_file = os.path.join(base_dir, ".download_tracker.json")
    if os.path.exists(tracker_file):
        with open(tracker_file, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Warning: Corrupt tracker file, starting fresh")
                return {'downloaded': [], 'failed': []}
    return {'downloaded': [], 'failed': []}

def save_download_tracker(base_dir, tracker_data):
    """Save the download tracker file"""
    tracker_file = os.path.join(base_dir, ".download_tracker.json")
    with open(tracker_file, 'w') as f:
        json.dump(tracker_data, f, indent=2)

def get_all_speeches(otter):
    """Fetch all speeches using pagination"""
    all_speeches = []
    folder = 0
    page_size = 45
    source = "all"
    seen_ids = set()
    last_ts = None
    page = 1
    
    with tqdm(desc="Fetching speeches", unit="page", ncols=100) as pbar:
        while True:
            print(f"\nFetching page {page} (timestamp: {last_ts})")
            response = otter.get_speeches(
                folder=folder,
                page_size=page_size,
                source=source,
                last_load_ts=last_ts
            )
            
            data = response['data']
            speeches = data.get('speeches', [])
            
            if not speeches:
                print("\nNo more speeches found")
                break
                
            # Add new speeches
            new_speeches = []
            for speech in speeches:
                speech_id = speech.get('speech_id')
                if speech_id not in seen_ids:
                    seen_ids.add(speech_id)
                    new_speeches.append(speech)
            
            if new_speeches:
                print(f"\nFetched {len(new_speeches)} new speeches:")
                for s in new_speeches[:5]:
                    print(f"- {s.get('title')} (ID: {s.get('speech_id')})")
                if len(new_speeches) > 5:
                    print(f"  ... and {len(new_speeches)-5} more")
                    
                all_speeches.extend(new_speeches)
                pbar.set_postfix({'total_unique': len(all_speeches), 
                                'new_this_page': len(new_speeches)})
            else:
                print("\nNo new speeches in this page")
                
            pbar.update(1)
            
            # Get next page timestamp
            last_ts = data.get('last_load_ts')
            if not last_ts or data.get('end_of_list', True):
                print(f"\nReached end of list")
                break
                
            page += 1
    
    return all_speeches

def main():
    try:
        print("Logging in to OtterAI...")
        otter = login()
        
        # Ensure base download directory exists
        base_dir = "downloads"
        os.makedirs(base_dir, exist_ok=True)
        
        # Load download tracker
        tracker = load_download_tracker(base_dir)
        
        print("\nFetching all speeches...")
        speeches = get_all_speeches(otter)
        
        if not speeches:
            print("No speeches found.")
            return
        
        print(f"\nFound {len(speeches)} total speeches")
        
        # Check existing downloads
        print("\nChecking existing downloads...")
        for dirpath, dirnames, filenames in os.walk(base_dir):
            if 'metadata.json' in filenames:
                try:
                    with open(os.path.join(dirpath, 'metadata.json')) as f:
                        metadata = json.load(f)
                        if 'speech_id' in metadata:
                            tracker['downloaded'].append(metadata['speech_id'])
                except:
                    continue
        
        print(f"Found {len(tracker['downloaded'])} existing downloads")
        
        # Filter out already downloaded speeches
        speeches_to_process = [
            s for s in speeches 
            if s['speech_id'] not in tracker['downloaded'] 
            and s['speech_id'] not in tracker['failed']
        ]
        
        print(f"Remaining to download: {len(speeches_to_process)}")
        print(f"Previously downloaded: {len(tracker['downloaded'])}")
        print(f"Previously failed: {len(tracker['failed'])}")
        
        if not speeches_to_process:
            print("No new speeches to download!")
            return
        
        # Process each speech with progress bar
        with tqdm(total=len(speeches_to_process), desc="Downloading speeches") as pbar:
            for speech in speeches_to_process:
                speech_dir = create_speech_directory(speech, base_dir)
                
                if download_speech_content(otter, speech, speech_dir):
                    tracker['downloaded'].append(speech['speech_id'])
                    pbar.set_postfix(successful=len(tracker['downloaded']))
                else:
                    tracker['failed'].append(speech['speech_id'])
                    pbar.set_postfix(failed=len(tracker['failed']))
                
                # Save progress after each speech
                save_download_tracker(base_dir, tracker)
                pbar.update(1)
        
        print(f"\nDownload complete!")
        print(f"Total successful: {len(tracker['downloaded'])}")
        print(f"Total failed: {len(tracker['failed'])}")
        
        if tracker['failed']:
            print("\nTo retry failed downloads, delete their IDs from .download_tracker.json")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
