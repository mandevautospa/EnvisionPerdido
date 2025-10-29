"""
Health check for Envision Perdido calendar

Checks:
- WordPress REST API reachable and authenticated
- Upcoming EventON events exist (using evcal_srow meta)
- Public calendar page loads and contains calendar markup

On failure, sends an email to NOTIFY_EMAIL (or RECIPIENT_EMAIL fallback).

Env vars expected:
- WP_SITE_URL, WP_USERNAME, WP_APP_PASSWORD
- SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, EMAIL_PASSWORD
- NOTIFY_EMAIL (fallback to RECIPIENT_EMAIL)
"""

from __future__ import annotations

import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from typing import Tuple, List

import requests
from requests.auth import HTTPBasicAuth


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def send_email(subject: str, html_body: str) -> None:
    smtp_server = get_env("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(get_env("SMTP_PORT", "587"))
    sender = get_env("SENDER_EMAIL", "")
    password = get_env("EMAIL_PASSWORD", "")
    recipient = get_env("NOTIFY_EMAIL", get_env("RECIPIENT_EMAIL", sender))

    if not (sender and password and recipient):
        log("Email not configured; skipping notification.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, [recipient], msg.as_string())


def wp_auth() -> Tuple[str, HTTPBasicAuth]:
    site = get_env("WP_SITE_URL", "https://sandbox.envisionperdido.org").rstrip("/")
    user = get_env("WP_USERNAME", "")
    app = get_env("WP_APP_PASSWORD", "")
    return site, HTTPBasicAuth(user, app)


def check_api_connection() -> Tuple[bool, str]:
    site, auth = wp_auth()
    try:
        r = requests.get(f"{site}/wp-json/wp/v2/users/me", auth=auth, timeout=15)
        if r.status_code == 200:
            name = r.json().get("name", "Unknown")
            return True, f"Connected to WP as {name}"
        return False, f"WP users/me returned {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, f"API connection error: {e}"


def fetch_events() -> Tuple[bool, List[dict] | None, str]:
    site, auth = wp_auth()
    try:
        # Fetch latest 100 published events
        r = requests.get(
            f"{site}/wp-json/wp/v2/ajde_events",
            params={"per_page": 100, "status": "publish", "orderby": "id", "order": "desc"},
            auth=auth,
            timeout=20,
        )
        if r.status_code == 200:
            return True, r.json(), "OK"
        return False, None, f"Events API returned {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, None, f"Events fetch error: {e}"


def count_upcoming(events: List[dict]) -> int:
    now_ts = int(datetime.now(timezone.utc).timestamp())
    cnt = 0
    for e in events:
        meta = e.get("meta", {})
        srow = meta.get("evcal_srow")
        try:
            srow_i = int(str(srow)) if srow is not None else 0
        except Exception:
            srow_i = 0
        if srow_i >= now_ts:
            cnt += 1
    return cnt


def check_calendar_page() -> Tuple[bool, str]:
    site, _ = wp_auth()
    url = f"{site}/events"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return False, f"Calendar page {url} returned {r.status_code}"
        html = r.text
        # Heuristic: EventON calendar markup
        if ("ajde_evcal" in html) or ("evo-calendar" in html) or ("evo_event" in html):
            return True, "Calendar page markup detected"
        return False, "Calendar page loaded but no EventON markup found"
    except Exception as e:
        return False, f"Calendar page error: {e}"


def main() -> int:
    threshold = int(os.getenv("HEALTH_MIN_UPCOMING", "5"))

    api_ok, api_msg = check_api_connection()
    log(api_msg)

    ev_ok, events, ev_msg = fetch_events()
    log(ev_msg if ev_ok else ev_msg)

    upcoming = count_upcoming(events or []) if ev_ok else 0
    log(f"Upcoming events count: {upcoming}")

    page_ok, page_msg = check_calendar_page()
    log(page_msg)

    ok = api_ok and ev_ok and page_ok and (upcoming >= threshold)

    if not ok:
        subject = "Community Calendar Health Check: ATTENTION Needed"
        body = f"""
        <h2>Calendar Health Check FAILED</h2>
        <ul>
          <li><b>API:</b> {api_msg}</li>
          <li><b>Events fetch:</b> {ev_msg}</li>
          <li><b>Upcoming count:</b> {upcoming} (threshold {threshold})</li>
          <li><b>Calendar page:</b> {page_msg}</li>
        </ul>
        <p>Investigate:
          <ol>
            <li>EventON plugin active and REST meta plugin active</li>
            <li>Recent events exist and are published</li>
            <li>Calendar page still configured</li>
          </ol>
        </p>
        """
        send_email(subject, body)
        return 2
    else:
        if get_env("HEALTH_SEND_OK", "false").lower() in {"true", "1", "yes"}:
            subject = "Community Calendar Health Check: OK"
            body = f"""
            <h2>Calendar Health Check OK</h2>
            <ul>
              <li><b>Upcoming events:</b> {upcoming}</li>
              <li><b>API:</b> {api_msg}</li>
              <li><b>Calendar page:</b> {page_msg}</li>
            </ul>
            """
            send_email(subject, body)
        return 0


if __name__ == "__main__":
    sys.exit(main())
