import discord
from discord.ext import tasks
import os
import asyncio
from datetime import datetime, timedelta
import pytz

# === ENABLE/DISABLE EVENTS ===
ENABLE_48H_EVENTS = True
ENABLE_WEEKLY_EVENTS = False  # Set to False to disable
ENABLE_BIWEEKLY_EVENTS = True

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

UTC = pytz.UTC

# === TRACK LAST RUN TIMES ===
last_run = {
    '48h_event_1': None,
    '48h_event_2': None,
    'weekly_event_1': None,
    'weekly_event_2': None,
    'biweekly_event_1': None,
    'biweekly_event_2': None
}

# === SET YOUR START DATES HERE ===
# For 48-hour events, set the first occurrence date and time (in UTC)
EVENT_48H_1_START = datetime(2025, 2, 13, 11, 20, 0)  # Example: Feb 14, 2025 at 18:00 UTC
EVENT_48H_2_START = datetime(2025, 2, 13, 19, 50, 0)  # Example: Feb 15, 2025 at 10:00 UTC

async def send_message(message):
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(message)

def should_run_event(event_key, now, cooldown_minutes=55):
    """
    Check if enough time has passed since the last run of this event.
    Uses a cooldown to prevent duplicate triggers.
    Default cooldown is 55 minutes (safe for hourly checks).
    """
    global last_run
    
    if last_run[event_key] is None:
        return True
    
    time_since_last = now - last_run[event_key]
    return time_since_last.total_seconds() >= (cooldown_minutes * 60)

def mark_event_run(event_key, now):
    """Mark an event as having run at the current time"""
    global last_run
    last_run[event_key] = now

def should_trigger_48h_event(start_date, now):
    """Check if a 48-hour interval event should trigger"""
    # Make start_date timezone-aware if it isn't
    if start_date.tzinfo is None:
        start_date = UTC.localize(start_date)
    
    # Calculate time difference
    time_diff = now - start_date
    
    # Check if we're past the start date
    if time_diff.total_seconds() < 0:
        return False
    
    # Check if we're at a 48-hour interval (within the current minute)
    hours_since_start = time_diff.total_seconds() / 3600
    intervals_passed = hours_since_start / 48
    
    # Check if we're at an interval boundary (within 1 minute tolerance)
    if abs(intervals_passed - round(intervals_passed)) < (1/60):
        return True
    
    return False

@tasks.loop(minutes=1)
async def scheduler():
    now = datetime.now(UTC)
    
    # === 48-HOUR INTERVAL EVENTS ===
    if ENABLE_48H_EVENTS:
        # EVENT 1 - every 48 hours from start date
        if should_trigger_48h_event(EVENT_48H_1_START, now) and should_run_event('48h_event_1', now, cooldown_minutes=2880):  # 48 hours - 1 hour
            await send_message("@everyone 🔥 Bear 1 starts in 10 minutes!")
            mark_event_run('48h_event_1', now)
        
        # EVENT 2 - every 48 hours from start date
        if should_trigger_48h_event(EVENT_48H_2_START, now) and should_run_event('48h_event_2', now, cooldown_minutes=2880):  # 48 hours - 1 hour
            await send_message("@everyone 🔥 Bear 2 starts in 10 minutes!")
            mark_event_run('48h_event_2', now)
    
    # === WEEKLY EVENTS ===
    if ENABLE_WEEKLY_EVENTS:
        # EVENT 3 - every Sunday at 14:00
        if now.weekday() == 6 and now.hour == 14 and now.minute == 0 and should_run_event('weekly_event_1', now, cooldown_minutes=10000):  # ~7 days
            await send_message("@everyone ⚔️ Weekly Event 1 starts now!")
            mark_event_run('weekly_event_1', now)
        
        # EVENT 4 - every Wednesday at 20:00
        if now.weekday() == 2 and now.hour == 20 and now.minute == 0 and should_run_event('weekly_event_2', now, cooldown_minutes=10000):  # ~7 days
            await send_message("@everyone 🎯 Weekly Event 2 starts now!")
            mark_event_run('weekly_event_2', now)
    
    # === BIWEEKLY EVENTS (every 2 weeks) ===
    if ENABLE_BIWEEKLY_EVENTS:
        # EVENT 5 - every other Friday at 18:00 (starting from a reference date)
        # Reference: First Friday of 2025 is Jan 3
        reference_date = datetime(2025, 1, 3, 18, 0, 0)
        if now.weekday() == 4 and now.hour == 18 and now.minute == 0:
            # Check if it's been an even number of weeks since reference
            days_diff = (now.date() - reference_date.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0 and should_run_event('biweekly_event_1', now, cooldown_minutes=20000):  # ~14 days
                await send_message("@everyone 🌟 Biweekly Event 1 starts now!")
                mark_event_run('biweekly_event_1', now)
        
        # EVENT 6 - every other Monday at 12:00 (starting from a reference date)
        # Reference: First Monday of 2025 is Jan 6
        reference_date_2 = datetime(2025, 1, 6, 12, 0, 0)
        if now.weekday() == 0 and now.hour == 12 and now.minute == 0:
            # Check if it's been an even number of weeks since reference
            days_diff = (now.date() - reference_date_2.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0 and should_run_event('biweekly_event_2', now, cooldown_minutes=20000):  # ~14 days
                await send_message("@everyone 👑 Biweekly Event 2 starts now!")
                mark_event_run('biweekly_event_2', now)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    print(f"Bot is monitoring events in channel ID: {CHANNEL_ID}")
    print(f"\nScheduled Events (all times in UTC):")
    print(f"  48h Events: {'ENABLED' if ENABLE_48H_EVENTS else 'DISABLED'}")
    if ENABLE_48H_EVENTS:
        print(f"    - Bear 1: Every 48 hours starting {EVENT_48H_1_START}")
        print(f"    - Bear 2: Every 48 hours starting {EVENT_48H_2_START}")
    print(f"  Weekly Events: {'ENABLED' if ENABLE_WEEKLY_EVENTS else 'DISABLED'}")
    if ENABLE_WEEKLY_EVENTS:
        print(f"    - Event 1: Every Sunday at 14:00 UTC")
        print(f"    - Event 2: Every Wednesday at 20:00 UTC")
    print(f"  Biweekly Events: {'ENABLED' if ENABLE_BIWEEKLY_EVENTS else 'DISABLED'}")
    if ENABLE_BIWEEKLY_EVENTS:
        print(f"    - Event 1: Every other Friday at 18:00 UTC")
        print(f"    - Event 2: Every other Monday at 12:00 UTC")
    scheduler.start()

client.run(TOKEN)
