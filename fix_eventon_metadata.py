"""
Fix EventON metadata for uploaded events

This script updates events 608-684 with proper EventON metadata fields
by making direct update calls with the metadata.
"""

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from requests.auth import HTTPBasicAuth
import time

# WordPress Configuration
WP_SITE_URL = "https://sandbox.envisionperdido.org"
WP_USERNAME = "jmiller"
WP_APP_PASSWORD = "GLAm Tlgz EUT7 b3S6 PNQJ JBVj"

auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
api_base = f"{WP_SITE_URL}/wp-json/wp/v2"

def log(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def update_event_metadata(event_id, event_data):
    """Update a single event with proper EventON metadata."""
    try:
        # Parse dates
        start_dt = pd.to_datetime(event_data['start'])
        
        # Build metadata
        metadata = {
            'evcal_srow': str(int(start_dt.timestamp())),
            'evcal_erow': str(int(start_dt.timestamp()) + 3600),  # Default 1 hour duration
            'evcal_start_date': start_dt.strftime('%m/%d/%Y'),
            'evcal_start_time_hour': start_dt.strftime('%I'),
            'evcal_start_time_min': start_dt.strftime('%M'),
            'evcal_start_time_ampm': start_dt.strftime('%p').lower(),
            'evcal_allday': 'no',
            'evo_hide_endtime': 'no',
            'evo_year_long': 'no',
            '_evcal_exlink_option': '1',
        }
        
        if pd.notna(event_data.get('end')):
            end_dt = pd.to_datetime(event_data['end'])
            metadata['evcal_erow'] = str(int(end_dt.timestamp()))
            metadata['evcal_end_date'] = end_dt.strftime('%m/%d/%Y')
            metadata['evcal_end_time_hour'] = end_dt.strftime('%I')
            metadata['evcal_end_time_min'] = end_dt.strftime('%M')
            metadata['evcal_end_time_ampm'] = end_dt.strftime('%p').lower()
        
        if pd.notna(event_data.get('url')):
            metadata['evcal_lmlink'] = str(event_data['url'])
        
        if pd.notna(event_data.get('location')):
            metadata['evcal_location_name'] = str(event_data['location'])
        
        # Update via REST API
        response = requests.post(
            f"{api_base}/ajde_events/{event_id}",
            auth=auth,
            json={'meta': metadata}
        )
        
        if response.status_code == 200:
            return True
        else:
            log(f"  ✗ Failed to update event {event_id}: {response.status_code}")
            log(f"     Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        log(f"  ✗ Error updating event {event_id}: {e}")
        return False

def main():
    """Main fix workflow."""
    print("\n" + "="*80)
    print("EVENTON METADATA FIX TOOL")
    print("="*80)
    
    # Load the CSV
    csv_path = Path("pipeline_output/calendar_upload_20251020_225559.csv")
    if not csv_path.exists():
        log(f"CSV file not found: {csv_path}")
        return
    
    log(f"Loading events from {csv_path}")
    df = pd.read_csv(csv_path)
    log(f"Found {len(df)} events to fix")
    
    # Events were created as IDs 608-684
    start_id = 608
    
    log("Updating EventON metadata for all events...")
    updated = 0
    
    for idx, row in df.iterrows():
        event_id = start_id + idx
        log(f"  Updating event {event_id}: {row['title'][:50]}")
        
        if update_event_metadata(event_id, row):
            updated += 1
            time.sleep(0.5)  # Be nice to the server
        
        if (idx + 1) % 10 == 0:
            log(f"  Progress: {idx + 1}/{len(df)} events processed")
    
    log(f"\n✓ Updated {updated}/{len(df)} events")
    log("Events should now appear in the calendar!")
    print("="*80)

if __name__ == "__main__":
    main()
