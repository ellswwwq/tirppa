import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
import hashlib
import re

URL = "https://www.tiira.fi/mielenkiintoiset2_PiLY.html"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SEEN_FILE = "lahetetyt_havainnot.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False)

def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

def fetch_observations():
    response = requests.get(URL)
    response.encoding = "latin1"

    soup = BeautifulSoup(response.text, "html.parser")

    lines = [
        " ".join(line.split())
        for line in soup.get_text("\n").splitlines()
        if line.strip()
    ]

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    observations = []

    for line in lines:

        if "tampere" not in line.lower():
            continue

        match = re.search(r"\b(\d{1,2}\.\d{1,2}\.\d{4})\b", line)

        if not match:
            continue

        try:
            obs_date = datetime.strptime(
                match.group(1),
                "%d.%m.%Y"
            ).date()

        except:
            continue

        if obs_date in [today, yesterday]:
            observations.append(line)

    return observations

def main():

    seen = load_seen()

    observations = fetch_observations()

    new_items = []

    for obs in observations:

        obs_id = hashlib.sha256(
            obs.encode("utf-8")
        ).hexdigest()

        if obs_id not in seen:
            new_items.append(obs)
            seen.add(obs_id)

    if new_items:

        message = (
            "Uudet Tampere-havainnot:\n\n"
            + "\n\n".join(new_items)
        )

        send_telegram(message)

        save_seen(seen)

if __name__ == "__main__":
    main()
