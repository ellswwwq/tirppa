import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# =========================
# ASETUKSET
# =========================

BOT_TOKEN = "OMA_BOT_TOKEN"

URL = "https://www.tiira.fi/mielenkiintoiset2_PiLY.html"

# =========================
# LOKIT
# =========================

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.INFO
)

# =========================
# HAVAINTOJEN HAKU
# =========================

def hae_havainnot():

    response = requests.get(URL, timeout=30)
    response.encoding = "latin1"

    soup = BeautifulSoup(response.text, "html.parser")

    lines = [
        " ".join(line.split())
        for line in soup.get_text("\n").splitlines()
        if line.strip()
    ]

    tanaan = datetime.now().strftime("%d.%m.%Y")

    kaikki = []
    tampere = []

    for line in lines:

        if tanaan not in line:
            continue

        kaikki.append(line)

        if "tampere" in line.lower():
            tampere.append(line)

    return kaikki, tampere

# =========================
# /tirppa KOMENTO
# =========================

async def tirppa(update: Update, context: ContextTypes.DEFAULT_TYPE):

    kaikki, _ = hae_havainnot()

    if not kaikki:
        await update.message.reply_text(
            "Kuluvan päivän havaintoja ei löytynyt."
        )
        return

    viesti = (
        "Kuluvan päivän havainnot:\n\n"
        + "\n\n".join(kaikki[:100])
    )

    # Telegramin viestiraja
    if len(viesti) > 4000:
        viesti = viesti[:4000]

    await update.message.reply_text(viesti)

# =========================
# AUTOMAATTINEN TAMPERE-KOOSTE
# =========================

async def laheta_tampere_kooste(context: ContextTypes.DEFAULT_TYPE):

    _, tampere = hae_havainnot()

    if not tampere:
        viesti = "Tänään ei löytynyt Tampere-havaintoja."

    else:
        viesti = (
            "Tampere-havainnot tänään:\n\n"
            + "\n\n".join(tampere)
        )

    if len(viesti) > 4000:
        viesti = viesti[:4000]

    for chat_id in context.bot_data["chat_ids"]:

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=viesti
            )

        except Exception as e:
            print(e)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if "chat_ids" not in context.bot_data:
        context.bot_data["chat_ids"] = set()

    context.bot_data["chat_ids"].add(chat_id)

    await update.message.reply_text(
        "Tirppabotti käynnissä.\n\n"
        "Komento:\n"
        "/tirppa"
    )

# =========================
# MAIN
# =========================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tirppa", tirppa))

    # Päivittäin klo 15
    app.job_queue.run_daily(
        laheta_tampere_kooste,
        time=datetime.strptime("15:00", "%H:%M").time()
    )

    print("Botti käynnissä")

    app.run_polling()

if __name__ == "__main__":
    main()
