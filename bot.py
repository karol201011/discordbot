import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TIMEZONE = "Europe/Warsaw"

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

def get_today_events():
    url = "https://www.forexfactory.com/calendar?day=today"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    rows = soup.find_all("tr", class_="calendar__row")

    for row in rows:
        impact = row.find("td", class_="calendar__impact")
        if not impact:
            continue

        impact_icon = impact.find("span")
        if not impact_icon:
            continue

        impact_title = impact_icon.get("title", "").lower()

        if "medium" not in impact_title and "high" not in impact_title:
            continue

        time = row.find("td", class_="calendar__time")
        currency = row.find("td", class_="calendar__currency")
        event = row.find("td", class_="calendar__event")

        if time and currency and event:
            events.append({
                "time": time.text.strip(),
                "currency": currency.text.strip(),
                "event": event.text.strip(),
                "impact": "🔴 High" if "high" in impact_title else "🟠 Medium"
            })

    return events

@tasks.loop(minutes=1)
async def daily_news():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)

    if now.hour == 0 and now.minute == 0 and now.weekday() < 5:
        channel = bot.get_channel(CHANNEL_ID)
        events = get_today_events()

        if not events:
            await channel.send("Brak wydarzeń na dziś.")
            return

        embed = discord.Embed(
            title="📊 Dzisiejsze wydarzenia Forex (Medium & High)",
            color=0xFFA500
        )

        for e in events:
            embed.add_field(
                name=f"{e['impact']} | {e['currency']}",
                value=f"🕒 {e['time']}\n📌 {e['event']}",
                inline=False
            )

        await channel.send(embed=embed)

@bot.event
async def on_ready():
    daily_news.start()

bot.run(TOKEN)
