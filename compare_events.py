"""Compare metadata between working event and our events"""
import requests
from requests.auth import HTTPBasicAuth
import json

auth = HTTPBasicAuth('jmiller', 'GLAm Tlgz EUT7 b3S6 PNQJ JBVj')

# Get an existing working event (ID 543)
print("=== EXISTING WORKING EVENT (ID 543) ===")
response = requests.get('https://sandbox.envisionperdido.org/wp-json/wp/v2/ajde_events/543', auth=auth)
if response.status_code == 200:
    event = response.json()
    meta = event.get('meta', {})
    
    # Filter for EventON-specific fields
    eventon_fields = {k: v for k, v in meta.items() if 'evcal' in k or 'evo_' in k or 'event_' in k}
    print("EventON metadata fields:")
    print(json.dumps(eventon_fields, indent=2))
else:
    print(f"Error: {response.status_code}")

print("\n" + "="*60)

# Get one of our events (ID 608)
print("=== OUR UPLOADED EVENT (ID 608) ===")
response = requests.get('https://sandbox.envisionperdido.org/wp-json/wp/v2/ajde_events/608', auth=auth)
if response.status_code == 200:
    event = response.json()
    meta = event.get('meta', {})
    
    # Filter for EventON-specific fields
    eventon_fields = {k: v for k, v in meta.items() if 'evcal' in k or 'evo_' in k or 'event_' in k}
    print("EventON metadata fields:")
    print(json.dumps(eventon_fields, indent=2))
else:
    print(f"Error: {response.status_code}")
