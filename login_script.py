#!/usr/bin/env python3

# Immediate test output at start of script
import sys
print("Script is running...", flush=True)

try:
    print("Testing stdout...", flush=True)
    sys.stdout.flush()
except Exception as e:
    sys.stderr.write(f"Error writing to stdout: {e}\n")
    sys.exit(1)

import os
from dotenv import load_dotenv

# Initialize these before imports to catch early errors
print("=== OtterAI Login Script ===")
print("Initializing...")

try:
    from otterai import OtterAI
    print("✓ OtterAI package imported successfully")
    print("Debug: OtterAI init signature:", OtterAI.__init__.__code__.co_varnames)
except ImportError as e:
    print("✗ Failed to import OtterAI package")
    print(f"Error details: {e}")
    print("\nPlease install the package using: pip install otterai")
    sys.exit(1)

def main():
    print("\nLoading environment variables...")
    load_dotenv()

    email = os.getenv('OTTER_USERNAME')
    password = os.getenv('OTTER_PASSWORD')

    if not email or not password:
        print("✗ Error: Missing credentials in .env file")
        print("Please ensure OTTER_USERNAME and OTTER_PASSWORD are set")
        sys.exit(1)

    print("✓ Credentials found in .env file")
    
    try:
        print("\nInitializing OtterAI client...")
        print(f"Attempting login for user: {email}")
        # Create instance first, then login
        otter = OtterAI()
        otter.login(email, password)  # Call login as a separate method
        print("✓ Successfully logged in to OtterAI")
        return otter
    except Exception as e:
        print("\n✗ Login failed!")
        print(f"Error details: {str(e)}")
        print("\nDebug information:")
        print(f"- Username configured: {'Yes' if email else 'No'}")
        print(f"- Password configured: {'Yes' if password else 'No'}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        otter = main()
        print("\n=== Login Successful ===")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
