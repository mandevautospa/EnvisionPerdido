"""
Delete test/duplicate events from WordPress calendar.

This script removes events created during testing to clean up the calendar.
Use with caution - deleted events cannot be recovered.
"""

import requests
import os
from requests.auth import HTTPBasicAuth
from datetime import datetime

def log(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def delete_events_range(start_id, end_id):
    """Delete events in the specified ID range."""
    
    # Get WordPress credentials from environment
    site_url = os.getenv("WP_SITE_URL", "https://sandbox.envisionperdido.org").rstrip('/')
    username = os.getenv("WP_USERNAME", "")
    app_password = os.getenv("WP_APP_PASSWORD", "")
    
    if not username or not app_password:
        log("ERROR: WordPress credentials not configured")
        return
    
    auth = HTTPBasicAuth(username, app_password)
    api_base = f"{site_url}/wp-json/wp/v2"
    
    # Test connection
    log("Testing WordPress API connection...")
    response = requests.get(f"{api_base}/users/me", auth=auth)
    
    if response.status_code != 200:
        log(f"ERROR: Authentication failed ({response.status_code})")
        return
    
    user_data = response.json()
    log(f"OK: Connected as {user_data.get('name', 'Unknown')}")
    
    # Delete events
    deleted = 0
    failed = 0
    
    log(f"Deleting events from ID {start_id} to {end_id}...")
    
    for event_id in range(start_id, end_id + 1):
        try:
            # Delete with force=true to permanently delete (skip trash)
            response = requests.delete(
                f"{api_base}/ajde_events/{event_id}",
                params={"force": True},
                auth=auth,
                timeout=10
            )
            
            if response.status_code == 200:
                deleted += 1
                if deleted % 10 == 0:
                    log(f"Deleted {deleted} events so far...")
            elif response.status_code == 404:
                # Event doesn't exist, skip silently
                pass
            else:
                failed += 1
                log(f"Failed to delete event {event_id}: {response.status_code}")
                
        except Exception as e:
            failed += 1
            log(f"Error deleting event {event_id}: {e}")
    
    log(f"\nCleanup complete:")
    log(f"  Deleted: {deleted} events")
    log(f"  Failed: {failed} events")
    log(f"  Total attempted: {end_id - start_id + 1}")

def main():
    """Main cleanup workflow."""
    print("\n" + "="*80)
    print("WORDPRESS EVENT CLEANUP")
    print("="*80)
    print("\nThis will PERMANENTLY DELETE events in the specified ID range.")
    print("Deleted events cannot be recovered.\n")
    
    # From testing, we created events with IDs 767-924
    print("Test run created events with IDs: 767-924")
    print("="*80)
    
    response = input("\nDelete events 767-924? (yes/no): ").strip().lower()
    
    if response == 'yes':
        delete_events_range(767, 924)
    else:
        log("Cleanup cancelled.")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
