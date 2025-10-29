"""Quick script to check if events exist in WordPress"""
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('jmiller', 'GLAm Tlgz EUT7 b3S6 PNQJ JBVj')
response = requests.get('https://sandbox.envisionperdido.org/wp-json/wp/v2/ajde_events?per_page=5', auth=auth)

print('Status:', response.status_code)
if response.status_code == 200:
    events = response.json()
    print(f'Found {len(events)} events (showing first 5)')
    for e in events:
        print(f"  - {e['title']['rendered']} (ID: {e['id']}, Status: {e['status']})")
else:
    print('Error:', response.text)
