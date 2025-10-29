"""Check event details to see why they're not showing"""
import requests
from requests.auth import HTTPBasicAuth
import json

auth = HTTPBasicAuth('jmiller', 'GLAm Tlgz EUT7 b3S6 PNQJ JBVj')

# Get one of our newly uploaded events
print("=== OUR NEWLY UPLOADED EVENT (ID 684) ===")
response = requests.get('https://sandbox.envisionperdido.org/wp-json/wp/v2/ajde_events/684', auth=auth)
if response.status_code == 200:
    event = response.json()
    print(f"Title: {event['title']['rendered']}")
    print(f"Status: {event['status']}")
    print(f"Date: {event.get('date', 'N/A')}")
    print(f"Meta fields: {list(event.get('meta', {}).keys())[:10]}")
    print(f"Full meta: {json.dumps(event.get('meta', {}), indent=2)[:500]}")
else:
    print(f"Error: {response.status_code}")

print("\n=== GETTING LIST OF ALL EVENTS (first 10) ===")
# Get all events to see what's there
response = requests.get('https://sandbox.envisionperdido.org/wp-json/wp/v2/ajde_events?per_page=100&orderby=id&order=asc', auth=auth)
if response.status_code == 200:
    events = response.json()
    print(f"Total events fetched: {len(events)}")
    
    # Show first few old events vs new events
    print("\nFirst 5 events (oldest):")
    for e in events[:5]:
        print(f"  ID {e['id']}: {e['title']['rendered'][:50]} - {e['status']}")
    
    print("\nLast 5 events (newest - should be ours):")
    for e in events[-5:]:
        print(f"  ID {e['id']}: {e['title']['rendered'][:50]} - {e['status']}")
        
    # Check if our event IDs are in there
    our_event_ids = list(range(608, 685))
    found_ids = [e['id'] for e in events if e['id'] in our_event_ids]
    print(f"\nOur events (608-684) found: {len(found_ids)}")
