#!/usr/bin/env python3

import sys
import json
from datetime import datetime
from login_script import main as login

def save_speeches(speeches, output_file=None):
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'speeches_{timestamp}.json'
    
    with open(output_file, 'w') as f:
        json.dump(speeches, f, indent=2)
    return output_file

def main():
    try:
        print("Logging in to OtterAI...")
        otter = login()
        
        print("\nFetching speeches...")
        speeches = otter.get_speeches()
        
        if not speeches or not isinstance(speeches, (list, dict)):
            print("No speeches found or invalid response format.")
            return
        
        # Handle potential response format (might be wrapped in a data field)
        if isinstance(speeches, dict):
            speeches = speeches.get('data', speeches)
        
        print(f"\nFound {len(speeches)} speeches")
        
        # Save speeches to file
        output_file = save_speeches(speeches)
        print(f"\nSaved speeches to: {output_file}")
        
        # Print summary
        print("\nSpeeches Summary:")
        for idx, speech in enumerate(speeches[:5], 1):
            title = speech.get('title', 'Untitled')
            date = speech.get('created_at', 'No date')
            id = speech.get('id', 'No ID')
            print(f"{idx}. [{id}] {title} - {date}")
        
        if len(speeches) > 5:
            print(f"... and {len(speeches) - 5} more")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
