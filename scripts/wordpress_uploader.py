"""
WordPress EventON Calendar Uploader

This script uploads classified community events to the WordPress calendar
using the WordPress REST API.

EventON uses a custom post type called 'ajde_events'.
"""

import requests
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import os
from requests.auth import HTTPBasicAuth

# WordPress Configuration
WORDPRESS_CONFIG = {
    "site_url": os.getenv("WP_SITE_URL", "https://sandbox.envisionperdido.org"),
    "username": os.getenv("WP_USERNAME", ""),  # WordPress admin username
    "app_password": os.getenv("WP_APP_PASSWORD", ""),  # WordPress Application Password
}

def log(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

class WordPressEventUploader:
    """Handle uploading events to WordPress EventON calendar."""
    
    def __init__(self, site_url, username, app_password):
        self.site_url = site_url.rstrip('/')
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self.auth = HTTPBasicAuth(username, app_password)
        self.session = requests.Session()
        
    def test_connection(self):
        """Test WordPress API connection and authentication."""
        log("Testing WordPress API connection...")
        
        try:
            # Test basic API access
            response = self.session.get(f"{self.api_base}/users/me", auth=self.auth)
            
            if response.status_code == 200:
                user_data = response.json()
                log(f"✓ Connected as: {user_data.get('name', 'Unknown')}")
                return True
            elif response.status_code == 401:
                log("✗ Authentication failed! Check username and app password.")
                return False
            else:
                log(f"✗ API error: {response.status_code}")
                return False
                
        except Exception as e:
            log(f"✗ Connection error: {e}")
            return False
    
    def get_event_locations(self):
        """Get existing event locations from WordPress."""
        try:
            response = self.session.get(
                f"{self.api_base}/event_location",
                auth=self.auth
            )
            if response.status_code == 200:
                return {loc['name']: loc['id'] for loc in response.json()}
            return {}
        except Exception as e:
            log(f"Warning: Could not fetch locations: {e}")
            return {}
    
    def create_or_get_location(self, location_name):
        """Create a new location or get existing location ID."""
        if not location_name or pd.isna(location_name):
            return None
        
        # Check existing locations
        locations = self.get_event_locations()
        if location_name in locations:
            return locations[location_name]
        
        # Create new location
        try:
            response = self.session.post(
                f"{self.api_base}/event_location",
                auth=self.auth,
                json={"name": location_name}
            )
            if response.status_code == 201:
                return response.json()['id']
        except Exception as e:
            log(f"Warning: Could not create location '{location_name}': {e}")
        
        return None
    
    def parse_event_metadata(self, event_row):
        """Parse event data into EventON metadata format."""
        metadata = {}
        
        # Event start and end times
        if pd.notna(event_row.get('start')):
            start_dt = pd.to_datetime(event_row['start'])
            metadata['evcal_srow'] = int(start_dt.timestamp())
            metadata['evcal_start_date'] = start_dt.strftime('%Y-%m-%d')
            metadata['evcal_start_time_hour'] = start_dt.strftime('%I')
            metadata['evcal_start_time_min'] = start_dt.strftime('%M')
            metadata['evcal_start_time_ampm'] = start_dt.strftime('%p').lower()
        
        if pd.notna(event_row.get('end')):
            end_dt = pd.to_datetime(event_row['end'])
            metadata['evcal_erow'] = int(end_dt.timestamp())
            metadata['evcal_end_date'] = end_dt.strftime('%Y-%m-%d')
            metadata['evcal_end_time_hour'] = end_dt.strftime('%I')
            metadata['evcal_end_time_min'] = end_dt.strftime('%M')
            metadata['evcal_end_time_ampm'] = end_dt.strftime('%p').lower()
        
        # Location
        if pd.notna(event_row.get('location')):
            location_id = self.create_or_get_location(str(event_row['location']))
            if location_id:
                metadata['event_location'] = location_id
        
        # URL
        if pd.notna(event_row.get('url')):
            metadata['evcal_lmlink'] = str(event_row['url'])
        
        return metadata
    
    def create_event(self, event_row):
        """Create a single event in WordPress."""
        try:
            # Prepare event data
            title = event_row.get('title', 'Untitled Event')
            description = event_row.get('description', '')
            
            # Parse metadata
            metadata = self.parse_event_metadata(event_row)
            
            # Create post data
            post_data = {
                'title': title,
                'content': description if pd.notna(description) else '',
                'status': 'draft',  # Start as draft for review
                'type': 'ajde_events',  # EventON custom post type
                'meta': metadata
            }
            
            # Send to WordPress
            response = self.session.post(
                f"{self.api_base}/ajde_events",
                auth=self.auth,
                json=post_data
            )
            
            if response.status_code == 201:
                event_data = response.json()
                log(f"✓ Created event: {title} (ID: {event_data['id']})")
                return event_data['id']
            else:
                log(f"✗ Failed to create event '{title}': {response.status_code}")
                log(f"   Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            log(f"✗ Error creating event '{event_row.get('title', 'Unknown')}': {e}")
            return None
    
    def upload_events_from_csv(self, csv_path, dry_run=True):
        """Upload events from CSV file."""
        log(f"Loading events from {csv_path}...")
        
        df = pd.read_csv(csv_path)
        log(f"Found {len(df)} events to upload")
        
        if dry_run:
            log("DRY RUN MODE - No events will be created")
            log("Review the following events:")
            for idx, row in df.iterrows():
                log(f"  - {row.get('title', 'Untitled')} ({row.get('start', 'No date')})")
            log(f"\nTo actually upload, run with dry_run=False")
            return []
        
        # Upload each event
        created_ids = []
        for idx, row in df.iterrows():
            event_id = self.create_event(row)
            if event_id:
                created_ids.append(event_id)
        
        log(f"Upload complete: {len(created_ids)}/{len(df)} events created")
        return created_ids
    
    def publish_events(self, event_ids):
        """Publish events that were created as drafts."""
        log(f"Publishing {len(event_ids)} events...")
        
        published = 0
        for event_id in event_ids:
            try:
                response = self.session.post(
                    f"{self.api_base}/ajde_events/{event_id}",
                    auth=self.auth,
                    json={'status': 'publish'}
                )
                if response.status_code == 200:
                    published += 1
            except Exception as e:
                log(f"Error publishing event {event_id}: {e}")
        
        log(f"Published {published}/{len(event_ids)} events")
        return published

def setup_wordpress_credentials():
    """Interactive setup for WordPress credentials."""
    print("\n" + "="*80)
    print("WORDPRESS CREDENTIALS SETUP")
    print("="*80)
    print("\nYou need WordPress Application Password for authentication.")
    print("To create one:")
    print("1. Log into WordPress admin")
    print("2. Go to Users → Profile")
    print("3. Scroll to 'Application Passwords'")
    print("4. Enter a name (e.g., 'Event Uploader') and click 'Add New'")
    print("5. Copy the generated password (it will look like: 'xxxx xxxx xxxx xxxx xxxx xxxx')")
    print("\n" + "="*80)
    
    site_url = input("\nWordPress Site URL (default: https://sandbox.envisionperdido.org): ").strip()
    if not site_url:
        site_url = "https://sandbox.envisionperdido.org"
    
    username = input("WordPress Username: ").strip()
    app_password = input("Application Password: ").strip()
    
    # Save to environment variables (for this session)
    os.environ["WP_SITE_URL"] = site_url
    os.environ["WP_USERNAME"] = username
    os.environ["WP_APP_PASSWORD"] = app_password
    
    print("\nCredentials set for this session.")
    print("To make permanent, add to your environment variables or .env file:")
    print(f"  WP_SITE_URL={site_url}")
    print(f"  WP_USERNAME={username}")
    print(f"  WP_APP_PASSWORD=<your_password>")
    
    return site_url, username, app_password

def main():
    """Main upload workflow."""
    print("\n" + "="*80)
    print("WORDPRESS CALENDAR UPLOADER")
    print("="*80)
    
    # Check for credentials
    if not WORDPRESS_CONFIG['username'] or not WORDPRESS_CONFIG['app_password']:
        log("WordPress credentials not found in environment variables.")
        site_url, username, app_password = setup_wordpress_credentials()
    else:
        site_url = WORDPRESS_CONFIG['site_url']
        username = WORDPRESS_CONFIG['username']
        app_password = WORDPRESS_CONFIG['app_password']
        log(f"Using credentials from environment for {username}")
    
    # Create uploader
    uploader = WordPressEventUploader(site_url, username, app_password)
    
    # Test connection
    if not uploader.test_connection():
        log("Cannot continue without valid WordPress connection.")
        return
    
    # Find latest calendar upload file
    base_dir = Path(__file__).parent.parent
    # Check new organized path first, fall back to legacy
    output_dir = base_dir / "output" / "pipeline"
    if not output_dir.exists():
        output_dir = base_dir / "pipeline_output"
    
    if not output_dir.exists():
        log(f"Output directory not found: {output_dir}")
        log("Please run the automated pipeline first to generate events.")
        return
    
    # Find most recent calendar upload file
    csv_files = list(output_dir.glob("calendar_upload_*.csv"))
    if not csv_files:
        log("No calendar upload files found.")
        log("Please run the automated pipeline first.")
        return
    
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    log(f"Using file: {latest_csv.name}")
    
    # Upload events (dry run first)
    print("\n" + "="*80)
    print("DRY RUN - Reviewing events before upload")
    print("="*80)
    uploader.upload_events_from_csv(latest_csv, dry_run=True)
    
    # Confirm upload
    print("\n" + "="*80)
    response = input("Upload these events to WordPress? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("\n" + "="*80)
        print("UPLOADING TO WORDPRESS")
        print("="*80)
        created_ids = uploader.upload_events_from_csv(latest_csv, dry_run=False)
        
        if created_ids:
            response = input(f"\n{len(created_ids)} events created as DRAFTS. Publish them? (yes/no): ").strip().lower()
            if response == 'yes':
                uploader.publish_events(created_ids)
                log("✓ Upload complete! Check your WordPress calendar.")
            else:
                log("Events saved as drafts. You can publish them manually in WordPress.")
    else:
        log("Upload cancelled.")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
