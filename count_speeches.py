#!/usr/bin/env python3

import sys
from login_script import main as login

def count_speeches(otter):
    """Quick count of total speeches"""
    response = otter.get_speeches(page_size=45, source="all")
    
    if not isinstance(response, dict) or 'status' not in response or response['status'] != 200:
        raise ValueError("Invalid response from API")
        
    data = response['data']
    speeches = data.get('speeches', [])
    total_in_page = len(speeches)
    
    print(f"First page has {total_in_page} speeches")
    print(f"Sample titles from first page:")
    for speech in speeches[:3]:
        print(f"- {speech.get('title')}")
        
    # Check for pagination info
    print("\nPagination info:")
    print(f"end_of_list: {data.get('end_of_list', False)}")
    if 'last_load_ts' in data:
        print(f"last_load_ts: {data['last_load_ts']}")
    
    return total_in_page

def main():
    try:
        print("Logging in to OtterAI...")
        otter = login()
        
        print("\nFetching first page of speeches...")
        count = count_speeches(otter)
        
        print(f"\nEstimated total (if 45 per page):")
        print(f"Current page shows: {count}")
        print(f"Current page count × 45: ~{count * 45} total speeches possible")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
