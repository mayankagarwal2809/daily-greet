#!/usr/bin/env python3
"""
Daily Greet Slack Bot 🐶
Posts a unique greeting to Slack every day via Incoming Webhook.

Usage:
    python3 slack_greet.py                    # Post today's greeting
    python3 slack_greet.py --preview 2        # Preview next N days (no posting)
    python3 slack_greet.py --test             # Post a test message

Requires:
    SLACK_WEBHOOK_URL environment variable (or .env file)
"""

import json
import math
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Greeting data (mirrors greetings.js — single source would be nicer, but
# keeping this self-contained avoids a Node dependency for a cron job)
# ---------------------------------------------------------------------------

def _load_greetings():
    """Load greetings from the shared JSON file (single source of truth)."""
    json_path = Path(__file__).parent / "greetings.json"
    if not json_path.exists():
        print(f"❌ greetings.json not found at {json_path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(json_path.read_text())


GREETINGS = _load_greetings()

# ---------------------------------------------------------------------------
# Date-seeded greeting picker (mirrors app.js lactly)
# ---------------------------------------------------------------------------

def get_day_of_year(d: date) -> int:
    return d.timetuple().tm_yday


def get_greeting_index(day_index: int, year: int) -> int:
    """Same hash as app.js — so Slack greeting matches the website."""
    seed = day_index * 2654435761 + year * 2246822519
    seed = seed & 0xFFFFFFFF  # Keep 32-bit
    seed = (((seed >> 16) ^ seed) * 0x45d9f3b) & 0xFFFFFFFF
    seed = (((seed >> 16) ^ seed) * 0x45d9f3b) & 0xFFFFFFFF
    seed = ((seed >> 16) ^ seed) & 0xFFFFFFFF
    return seed % len(GREETINGS)


def get_greeting_for_date(d: date) -> dict:
    idx = get_greeting_index(get_day_of_year(d), d.year)
    return GREETINGS[idx]


# ---------------------------------------------------------------------------
# Slack posting
# ---------------------------------------------------------------------------

def load_webhook_url() -> str:
    """Load webhook URL from env or .env file."""
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if url:
        return url

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("SLACK_WEBHOOK_URL="):
                return line.split("=", 1)[1].strip().strip("\"'")

    print("❌ SLACK_WEBHOOK_URL not set!", file=sys.stderr)
    print("   Set it via: export SLACK_WEBHOOK_URL='https://hooks.slack.com/...'", file=sys.stderr)
    print("   Or add it to .env in this directory.", file=sys.stderr)
    sys.exit(1)


def build_slack_message(greeting: dict, d: date) -> dict:
    """Build a rich Slack Block Kit message."""
    date_str = d.strftime("%A, %B %-d, %Y")
    day_num = get_day_of_year(d)

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{greeting['emoji']}  Daily Greet — {date_str}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{greeting['text']}*",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"💡 *Tip:* {greeting['tip']}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"📂 _{greeting['category']}_  •  Day {day_num}/365",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "👋 <https://daily-greet.vercel.app|View all greetings on Daily Greet>",
                    }
                ],
            },
        ]
    }


def post_to_slack(webhook_url: str, message: dict) -> bool:
    """Post a message to Slack via Incoming Webhook."""
    data = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    # Respect Walmart proxy
    proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if proxy_url:
        proxy_handler = urllib.request.ProxyHandler({
            "https": proxy_url,
            "http": proxy_url,
        })
        opener = urllib.request.build_opener(proxy_handler)
    else:
        opener = urllib.request.build_opener()

    try:
        response = opener.open(req, timeout=10)
        return response.status == 200
    except Exception as e:
        print(f"❌ Failed to post to Slack: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def preview_greetings(days: int):
    """Preview upcoming greetings without posting."""
    today = date.today()
    print(f"\n🔮 Preview: Next {days} day(s) of greetings\n{'─' * 50}")
    for i in range(days):
        d = today + timedelta(days=i)
        g = get_greeting_for_date(d)
        label = "TODAY ➜" if i == 0 else f"Day +{i} ➜"
        print(f"\n{label} {d.strftime('%A, %b %-d')}")
        print(f"   {g['emoji']}  {g['text']}")
        print(f"   💡 {g['tip']}")
        print(f"   📂 {g['category']}")
    print(f"\n{'─' * 50}")


def main():
    args = sys.argv[1:]

    if "--preview" in args:
        idx = args.index("--preview")
        days = int(args[idx + 1]) if idx + 1 < len(args) else 7
        preview_greetings(days)
        return

    webhook_url = load_webhook_url()

    if "--test" in args:
        test_msg = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "🧪 *Daily Greet test message!* If you see this, the webhook is working! 🎉",
                    },
                }
            ]
        }
        ok = post_to_slack(webhook_url, test_msg)
        print("✅ Test message sent!" if ok else "❌ Test failed.")
        return

    # Post today's greeting
    today = date.today()
    greeting = get_greeting_for_date(today)
    message = build_slack_message(greeting, today)

    print(f"📤 Posting greeting for {today.strftime('%A, %b %-d')}...")
    print(f"   {greeting['emoji']}  {greeting['text']}")

    ok = post_to_slack(webhook_url, message)
    if ok:
        print("✅ Greeting posted to Slack!")
    else:
        print("❌ Failed to post. Check your webhook URL.")
        sys.exit(1)


if __name__ == "__main__":
    main()
