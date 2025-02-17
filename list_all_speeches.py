#!/usr/bin/env python3

import sys
import json
from datetime import datetime, timezone
from login_script import main as login

def inspect_api_call(otter, last_ts=None):
    """Make API call and inspect details"""
    speeches_url = f"{otter.API_BASE_URL}speeches"
    
    # Match web interface query parameters exactly
    params = {
        'userid': otter._userid,
        'folder': 0,
        'page_size': 45,
        'source': 'home',
        'speech_metadata': 'true',
        'funnel': 'home_feed'
    }

    # Add pagination parameters exactly as web interface does
    if last_ts:
        params['last_load_ts'] = last_ts
        # Get current time in seconds since epoch
        current_ts = int(datetime.now(timezone.utc).timestamp())
        params['modified_after'] = current_ts
    
    headers = {
        'x-client-version': 'Otter v3.68.1',
        'x-csrftoken': otter._cookies['csrftoken'],
        'referer': 'https://otter.ai/'
    }
    
    print("\nMaking request:")
    print(f"URL: {speeches_url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    
    response = otter._session.get(speeches_url, params=params, headers=headers)
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
    
    try:
        data = response.json()
        print("\nResponse Data:")
        print(json.dumps({k:v for k,v in data.items() if k != 'speeches'}, indent=2))
        return data
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None

def main():
    print("Logging in to OtterAI...")
    otter = login()
    
    all_speeches = []
    seen_ids = set()
    page = 1
    last_ts = None
    
    try:
        while True:
            print(f"\n=== Page {page} ===")
            data = inspect_api_call(otter, last_ts)
            
            if not data or data.get('status') != 'OK':
                print("Invalid response")
                break
                
            speeches = data.get('speeches', [])
            if not speeches:
                print("No speeches found")
                break
                
            # Process speeches
            new_count = 0
            for speech in speeches:
                if speech['speech_id'] not in seen_ids:
                    seen_ids.add(speech['speech_id'])
                    all_speeches.append(speech)
                    new_count += 1
            
            print(f"\nNew speeches this page: {new_count}")
            print(f"Sample from this page:")
            for s in speeches[:3]:
                created = datetime.fromtimestamp(s.get('created_at', 0))
                print(f"- {s.get('title')}")
                print(f"  ID: {s.get('speech_id')}")
                print(f"  Created: {created}")
            if len(speeches) > 3:
                print(f"  ... and {len(speeches)-3} more")
                
            print(f"\nTotal unique speeches: {len(all_speeches)}")
            
            # Get next timestamp
            last_ts = data.get('last_load_ts')
            print(f"Next page timestamp: {last_ts}")
            
            if data.get('end_of_list'):
                print("Reached end of list")
                break
                
            if not last_ts:
                print("No timestamp for next page")
                break
                
            choice = input("\nFetch next page? [Y/n]: ")
            if choice.lower().startswith('n'):
                break
                
            page += 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled")

    # Save results
    if all_speeches:
        with open('speeches_list.json', 'w') as f:
            json.dump({
                'total_count': len(all_speeches),
                'speeches': all_speeches,
                'unique_ids': list(seen_ids)
            }, f, indent=2)
        print(f"\nSaved {len(all_speeches)} speeches to speeches_list.json")
    else:
        print("\nNo speeches were collected")

if __name__ == "__main__":
    main()
