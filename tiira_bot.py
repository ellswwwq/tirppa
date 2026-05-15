import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

URL = "https://www.tiira.fi/mielenkiintoiset2_PiLY.html"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_telegram(message):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=30
    )

    response.raise_for_status()


def fetch_tampere_observations():
    response = requests.get(URL, timeout=30)
    response.encoding = "latin1"
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n")

    raw_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    allowed_dates = {today, yesterday}

    current_year = today.year
    current_date = None
    current_species = None
    observations = []

    for line in raw_lines:
        date_match = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.", line)

        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            current_date = datetime(current_year, month, day).date()
            current_species = None
            continue

        if current_date not in allowed_dates:
            continue

        if line.startswith("("):
            continue

        if " " not in line:
            current_species = line
            continue

        if "tampere" in line.lower():
            if current_species:
                observations.append(f"{current_species} {line}")
            else:
                observations.append(line)

    return observations


def split_message(text, max_length=3900):
    parts = []

    while len(text) > max_length:
        split_at = text.rfind("\n\n", 0, max_length)

        if split_at == -1:
            split_at = max_length

        parts.append(text[:split_at])
        text = text[split_at:].strip()

    if text:
        parts.append(text)

    return parts


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN puuttuu GitHub Secrets -asetuksista.")

    if not CHAT_ID:
        raise ValueError("CHAT_ID puuttuu GitHub Secrets -asetuksista.")

    observations = fetch_tampere_observations()

    today_text = datetime.now().strftime("%d.%m.%Y")
    yesterday_text = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")

    if not observations:
        message = (
            f"Tampere-havainnot {yesterday_text} ja {today_text}:\n\n"
            "Ei havaintoja."
        )
        send_telegram(message)
        return

    message = (
        f"Tampere-havainnot {yesterday_text} ja {today_text}:\n\n"
        + "\n\n".join(observations)
    )

    for part in split_message(message):
        send_telegram(part)


if __name__ == "__main__":
    main()
