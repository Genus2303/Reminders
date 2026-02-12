import discord
from discord.ext import tasks
import os
import asyncio
from datetime import datetime
import pytz

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

UK = pytz.timezone("Europe/London")

async def send_message(message):
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(message)

@tasks.loop(minutes=1)
async def scheduler():
    now = datetime.now(UK)

    # EVENT 1 - every 2 days at 18:00
    if now.hour == 10 and now.minute == 54 and now.day % 2 == 0:
        await send_message("@everyone 🔥 Event 1 starts now!")

    # EVENT 2 - weekly Sunday at 14:00
    if now.weekday() == 6 and now.hour == 14 and now.minute == 0:
        await send_message("@everyone ⚔ Weekly Event starts now!")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    scheduler.start()

client.run(TOKEN)

