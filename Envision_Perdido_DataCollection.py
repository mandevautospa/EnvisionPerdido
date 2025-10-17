import time, re, csv, json
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar
import os
import re
import time
import csv
import json


BASE = "https://business.perdidochamber.com"

#Month view of calendar
MONTH_URL = "https://business.perdidochamber.com/events/calendar"

sess = requests.Session()
sess.headers.update({
    # mimics a browser to prevent the scraper from being blocked
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
})

## SiteMap URL: https://business.perdidochamber.com/SiteMap.xml
## List of all URL's we can scrape according to their robots.txt
## https://business.perdidochamber.com/robots.txt

#helper function to get full URL
def get_event_url(month_url):

    #sending the HTTP request to the calendar page
    response = sess.get(month_url, timeout=30)
    response.raise_for_status()

    #parsing the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')

    #collecting the event detail links
    event_links = []
    for anchor in soup.select('a[href*="/events/details"]'):
            href = anchor.get('href')
            if href:
                event_links.append(urljoin(BASE, href))

    #delete the redundant copies while preserving the order
    seen, unique_links = set(), []
    for link in event_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    return unique_links

def find_ics_links(soup: BeautifulSoup) -> str | None:
    anchor = soup.find('a', string=re.compile(r'Add to Calendar\s*-\s*iCal', re.IGNORECASE))
    if anchor and anchor.get('href'):
        return urljoin(BASE, anchor['href'])
    
    generic = soup.select_one('a[href$=".ics"]')
    if generic and generic.get('href'):
        return urljoin(BASE, generic['href'])
    
    return None

def get_ics_url_from_event(event_url: str) -> str | None:
    """Fetches the ICS URL from the event page.
    
       GrowthZone event detail pages include an "Add to Calendar -> iCal" link 
       that points to an ICS file. If that link cannot be found, this function
       falls back to constructing the .ics URL from the event detil slug.

       Args:
           event_url (str): The URL of the event detail page.

       Returns:
           str | None: The URL of the ICS file, or None if it cannot be found.
    """
    try:
        time.sleep(1)  # be polite and avoid overwhelming the server
        response = sess.get(event_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching event page {event_url}: {e}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for the "Add to Calendar -> iCal" link
    ics_link = find_ics_links(soup)
    if ics_link:
        return ics_link
    
    # Fallback: Construct the ICS URL from the event detail slug
    match = re.search(r'/events/details/([^/]+)', urlparse(event_url).path)
    if match:
        event_slug = match.group(1)
        return urljoin(BASE, f"/events/ical/{event_slug}.ics")
    else:
        print(f"Warning: Unexpected event URL format: {event_url}")
    
    return None

#ics fetching and parsing 
def fetch_calendar(ics_url:str) -> Calendar | None:

    #download and parse the ics file into an icalendar object
    try:
        time.sleep(1)  # be polite and avoid overwhelming the server
        response = sess.get(ics_url, timeout=30)
        response.raise_for_status()
        return Calendar.from_ical(response.content)
    except requests.RequestException as e:
        print(f"Error fetching ICS file {ics_url}: {e}")
    except Exception as e:
        print(f"Error parsing ICS file from {ics_url}: {e}")
    
    return None

def _dt_to_iso(v):
    #handle date or tatetime with or without timezone return ISO format string

    if not v:
        return None
    
    #icalendar stores time as vDDDTypes; .dt can be date or datetime
    dt = getattr(v, 'dt', v)
    
    try:
        #if its a date, return YYYY-MM-DD
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        
        #fallback: convert to string
        return str(dt)
    except Exception:
        return str(dt)

def _text_or_none(val):
    return str(val) if val is not None else None

def parse_calendar_to_events(cal: Calendar, source_ics: str, source_page: str | None = None) -> list[dict]:
    # extract VEVENTS into a list of normalized dicts
    events = []
    if cal is None:
        return events
    
    for component in cal.walk('VEVENT'):
        summary = _text_or_none(component.get('SUMMARY'))
        description = _text_or_none(component.get('DESCRIPTION'))
        location = _text_or_none(component.get('LOCATION'))
        url = _text_or_none(component.get('URL'))
        uid = _text_or_none(component.get('UID'))
        category = _text_or_none(component.get('CATEGORIES'))
        if category is not None:
            #categories can be a vText or list-like; normalize
            try:
                category = list(category.cats)
            except Exception:
                category = [_text_or_none(category)]

        event = {
            "title": summary,
            "description": description,
            "location": location,
            "start": _dt_to_iso(component.get('DTSTART')),
            "end": _dt_to_iso(component.get('DTEND')),
            "url": url,
            "uid": uid,
            "category": category,
            "last_modified": _dt_to_iso(component.get('LAST-MODIFIED')),
            "created": _dt_to_iso(component.get('CREATED')),

            #provencence
            "source_ics": source_ics,
            "source_page": source_page
        }

        events.append(event)
        
    return events

def scrape_month(month_url: str, pause_seconds: float = 0.4) -> list[dict]:
    # Scrape all events from a month view URL
    all_events: list[dict] = []
    errors: list[str] = []

    try:
        event_pages = get_event_url(month_url)
    except Exception as e:
        print(f"Error fetching event URLs from {month_url}: {e}")
        return all_events   
    print(f"Found {len(event_pages)} event pages in month view.")

    seen_ics: set[str] = set()
    for i, page_url in enumerate(event_pages, 1):
        try:
            ics = get_ics_url_from_event(page_url)
            if not ics:
                errors.append(f"No ICS link found on event page {page_url}")
                continue    

            if ics in seen_ics:
                continue
            seen_ics.add(ics)

            cal = fetch_calendar(ics)
            events = parse_calendar_to_events(cal, source_ics=ics, source_page=page_url)
            all_events.extend(events)
        except Exception as e:
            errors.append(f"Error processing event page {page_url}: {e}")
        finally:
            time.sleep(pause_seconds)  # be polite and avoid overwhelming the server

    print(f"Scraped {len(all_events)} events with {len(errors)} errors.")
    if errors:
        for msg in errors[:5]:
            print(f"  - {msg}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors.")
    return all_events

#save to JSON/csv
def save_events_json(events: list[dict], path: str = "perdido_events.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def save_events_csv(events: list[dict], path: str = "perdido_events.csv"):   
    if not events:
        print("No events to save.")
        return

    cols = [
        "title", "start", "end", "location", "url",
        "description", "uid", "category",
    ]         

    #flatten categories
    def rowify(e):
        r = {k: e.get(k) for k in cols}
        if isinstance(r.get("category"), list):
            r["category"] = ";".join(filter(None, map(str, r["category"])))
        return r
    
    with open(path, "w", newline = "", encoding = "utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for event in events:
            writer.writerow(rowify(event))

if __name__ == "__main__":
    print("[runner] starting scrape...", flush=True)

    #  prove network works & page is reachable
    try:
        r = sess.get(MONTH_URL, timeout=15)
        #status code 200 means the request was successful
        print(f"[runner] GET {MONTH_URL} -> {r.status_code}, bytes={len(r.content)}", flush=True)
    except Exception as e:
        print(f"[runner] failed to reach month page: {e}", flush=True)

    events = scrape_month(MONTH_URL)
    print(f"[runner] scraped {len(events)} events", flush=True)

    # Save to absolute paths so you know exactly where they land
    OUT_DIR = "/Users/jacob/codeWorkspace/ResearchLab/EnvisionPerdido"
    os.makedirs(OUT_DIR, exist_ok=True)
    json_path = os.path.join(OUT_DIR, "perdido_events.json")
    csv_path  = os.path.join(OUT_DIR, "perdido_events.csv")

    save_events_json(events, json_path)
    save_events_csv(events, csv_path)

    print(f"[runner] wrote:\n  - {json_path}\n  - {csv_path}", flush=True)
    print("[done]", flush=True)
    
    #import subprocess, sys
    #subprocess.run(sys.executable, "scripts/tag_events.py", check=True)

    

