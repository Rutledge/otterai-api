#!/usr/bin/env python3

import os
import sys
import json
from datetime import datetime
from tqdm import tqdm
from login_script import main as login

def get_speech_id(speech):
    """Get the correct ID for downloading a speech"""
    # Try different possible ID fields in order
    speech_id = speech.get('otid')  # Primary ID for downloads
    if not speech_id:
        speech_id = speech.get('speech_id')  # Fallback to speech_id
    return speech_id

def create_speech_dir(speech, base_dir="downloads"):
    """Create a directory for the speech with clean name"""
    try:
        # Get timestamp and clean title
        created = datetime.fromtimestamp(speech.get('created_at', 0))
        date_str = created.strftime('%Y-%m-%d')
        
        # Clean title - handle None case
        title = (speech.get('title') or 'Untitled').strip()
        title = ''.join(c for c in title if c.isalnum() or c in ' -_')
        
        # Get speech ID
        speech_id = get_speech_id(speech)
        if not speech_id:
            raise ValueError("No valid speech ID found")
            
        # Create directory name
        dir_name = f"{date_str}_{title}_{speech_id[:8]}"[:80]
        dir_name = dir_name.strip()
        
        # Create directory
        full_path = os.path.join(base_dir, dir_name)
        os.makedirs(full_path, exist_ok=True)
        
        return full_path
        
    except Exception as e:
        print(f"Error creating directory: {e}")
        # Create fallback directory
        fallback_dir = os.path.join(base_dir, "error_downloads")
        os.makedirs(fallback_dir, exist_ok=True)
        return fallback_dir

def download_speech(otter, speech, directory):
    """Download speech content and metadata"""
    try:
        # Get proper speech ID
        speech_id = get_speech_id(speech)
        if not speech_id:
            print("No valid speech ID found")
            return False
            
        title = speech.get('title') or 'Untitled'
        
        print(f"\nDownloading: {title}")
        print(f"ID: {speech_id}")
        print(f"Directory: {directory}")
        
        # Save metadata first
        metadata_file = os.path.join(directory, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(speech, f, indent=2)
        print("✓ Saved metadata")
        
        # Download content
        base_name = os.path.join(directory, speech_id)
        print(f"Downloading content to: {base_name}.zip")
        
        result = otter.download_speech(
            speech_id=speech_id,
            name=base_name,
            fileformat="txt,pdf,mp3,docx,srt"
        )
        
        # Verify download
        zip_path = f"{base_name}.zip"
        if os.path.exists(zip_path):
            size = os.path.getsize(zip_path) / (1024*1024)
            print(f"✓ Downloaded {size:.1f}MB zip file")
            return True
            
        print(f"✗ Failed to find zip file at {zip_path}")
        return False
        
    except Exception as e:
        print(f"✗ Error downloading speech: {e}")
        return False

def main():
    # Load speech list
    if not os.path.exists('speeches_list.json'):
        print("speeches_list.json not found! Run list_all_speeches.py first")
        sys.exit(1)
        
    with open('speeches_list.json') as f:
        data = json.load(f)
        speeches = data.get('speeches', [])

    if not speeches:
        print("No speeches found in speeches_list.json")
        sys.exit(1)

    print(f"Found {len(speeches)} speeches to process")
    
    # Load progress tracker
    progress_file = 'download_progress.json'
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            progress = json.load(f)
    else:
        progress = {'downloaded': [], 'failed': []}
    
    # Filter already processed
    to_download = [s for s in speeches 
                  if s['speech_id'] not in progress['downloaded']
                  and s['speech_id'] not in progress['failed']]
    
    print(f"Already downloaded: {len(progress['downloaded'])}")
    print(f"Previously failed: {len(progress['failed'])}")
    print(f"Remaining to download: {len(to_download)}")
    
    if not to_download:
        print("Nothing new to download!")
        return
        
    # Login and start downloads
    print("\nLogging in to OtterAI...")
    otter = login()

    # Create downloads directory
    os.makedirs("downloads", exist_ok=True)
    
    print("\nDownloads will be saved to ./downloads/")
    print("Each speech will include:")
    print("- metadata.json: Speech details")
    print("- {speech_id}.zip: All formats (txt,pdf,mp3,docx,srt)")
    
    if input("\nContinue? [Y/n]: ").lower().startswith('n'):
        return
    
    with tqdm(total=len(to_download), desc="Downloading") as pbar:
        for speech in to_download:
            speech_id = speech['speech_id']
            directory = create_speech_dir(speech)
            
            pbar.set_description(f"Downloading {speech_id}")
            
            if download_speech(otter, speech, directory):
                progress['downloaded'].append(speech_id)
                pbar.set_postfix(success=len(progress['downloaded']))
            else:
                progress['failed'].append(speech_id)
                pbar.set_postfix(failed=len(progress['failed']))
            
            # Save progress after each download
            with open(progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
                
            pbar.update(1)
    
    print("\nDownload complete!")
    print(f"Successfully downloaded: {len(progress['downloaded'])}")
    print(f"Failed downloads: {len(progress['failed'])}")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
