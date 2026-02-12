import discord
from discord.ext import tasks
import os
import asyncio
from datetime import datetime, timedelta
import pytz

# === ENABLE/DISABLE EVENTS ===
ENABLE_48H_EVENTS = True
ENABLE_WEEKLY_EVENTS = False  # Set to False to disable
ENABLE_BIWEEKLY_EVENTS = False

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

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
EVENT_48H_1_START = datetime(2026, 2, 13, 11, 20, 0)  # Example: Feb 14, 2025 at 18:00 UTC
EVENT_48H_2_START = datetime(2026, 2, 13, 19, 50, 0)  # Example: Feb 15, 2025 at 10:00 UTC

async def send_message(message):
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
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

def format_time_remaining(td):
    """Format a timedelta into a human-readable string"""
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 0:
        return "Event is overdue!"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    return " ".join(parts) if parts else "Less than 1 minute"

def get_next_48h_event_time(start_date, now):
    """Calculate the next occurrence of a 48-hour event"""
    if start_date.tzinfo is None:
        start_date = UTC.localize(start_date)
    
    time_diff = now - start_date
    
    # If we haven't reached the start date yet
    if time_diff.total_seconds() < 0:
        return start_date
    
    # Calculate how many intervals have passed
    hours_since_start = time_diff.total_seconds() / 3600
    intervals_passed = int(hours_since_start / 48)
    
    # Next occurrence is the next interval
    next_interval = intervals_passed + 1
    next_time = start_date + timedelta(hours=next_interval * 48)
    
    return next_time

def get_next_weekly_event_time(target_weekday, target_hour, target_minute, now):
    """Calculate the next occurrence of a weekly event"""
    current_weekday = now.weekday()
    days_until = (target_weekday - current_weekday) % 7
    
    next_date = now.date() + timedelta(days=days_until)
    next_time = datetime.combine(next_date, datetime.min.time()).replace(
        hour=target_hour, minute=target_minute, tzinfo=UTC
    )
    
    # If it's today but the time has passed, go to next week
    if next_time <= now:
        next_time += timedelta(days=7)
    
    return next_time

def get_next_biweekly_event_time(reference_date, target_weekday, target_hour, target_minute, now):
    """Calculate the next occurrence of a biweekly event"""
    if reference_date.tzinfo is None:
        reference_date = UTC.localize(reference_date)
    
    # Find the next occurrence of the target weekday
    current_weekday = now.weekday()
    days_until = (target_weekday - current_weekday) % 7
    
    candidate_date = now.date() + timedelta(days=days_until)
    candidate_time = datetime.combine(candidate_date, datetime.min.time()).replace(
        hour=target_hour, minute=target_minute, tzinfo=UTC
    )
    
    # If it's today but the time has passed, move to next occurrence of this weekday
    if candidate_time <= now:
        candidate_time += timedelta(days=7)
        candidate_date = candidate_time.date()
    
    # Check if this falls on the correct biweekly cycle
    days_diff = (candidate_date - reference_date.date()).days
    weeks_diff = days_diff // 7
    
    # If not on the correct cycle, add one more week
    if weeks_diff % 2 != 0:
        candidate_time += timedelta(days=7)
    
    return candidate_time

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
    # AND check that we're in the exact minute (hour and minute match)
    interval_number = round(intervals_passed)
    expected_time = start_date + timedelta(hours=interval_number * 48)
    
    # Must match hour AND minute exactly
    if now.hour == expected_time.hour and now.minute == expected_time.minute:
        if abs(intervals_passed - interval_number) < (1/60):
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

@tree.command(name="events", description="Show when all events are scheduled")
async def show_events(interaction: discord.Interaction):
    """Display all upcoming events with countdowns"""
    now = datetime.now(UTC)
    
    embed = discord.Embed(
        title="📅 SEA Events Schedule 💜",
        description="All times are in UTC",
        color=discord.Color.blue()
    )
    
    # 48-hour events
    if ENABLE_48H_EVENTS:
        next_bear1 = get_next_48h_event_time(EVENT_48H_1_START, now)
        next_bear2 = get_next_48h_event_time(EVENT_48H_2_START, now)
        
        time_to_bear1 = next_bear1 - now
        time_to_bear2 = next_bear2 - now
        
        embed.add_field(
            name="🔥 Bear 1 (Every 48 hours)",
            value=f"Next: <t:{int(next_bear1.timestamp())}:F>\nIn: **{format_time_remaining(time_to_bear1)}**",
            inline=False
        )
        embed.add_field(
            name="🔥 Bear 2 (Every 48 hours)",
            value=f"Next: <t:{int(next_bear2.timestamp())}:F>\nIn: **{format_time_remaining(time_to_bear2)}**",
            inline=False
        )
    
    # Weekly events
    if ENABLE_WEEKLY_EVENTS:
        next_weekly1 = get_next_weekly_event_time(6, 14, 0, now)  # Sunday 14:00
        next_weekly2 = get_next_weekly_event_time(2, 20, 0, now)  # Wednesday 20:00
        
        time_to_weekly1 = next_weekly1 - now
        time_to_weekly2 = next_weekly2 - now
        
        embed.add_field(
            name="⚔️ Weekly Event 1 (Sundays 14:00)",
            value=f"Next: <t:{int(next_weekly1.timestamp())}:F>\nIn: **{format_time_remaining(time_to_weekly1)}**",
            inline=False
        )
        embed.add_field(
            name="🎯 Weekly Event 2 (Wednesdays 20:00)",
            value=f"Next: <t:{int(next_weekly2.timestamp())}:F>\nIn: **{format_time_remaining(time_to_weekly2)}**",
            inline=False
        )
    
    # Biweekly events
    if ENABLE_BIWEEKLY_EVENTS:
        reference_date = datetime(2025, 1, 3, 18, 0, 0)
        reference_date_2 = datetime(2025, 1, 6, 12, 0, 0)
        
        next_biweekly1 = get_next_biweekly_event_time(reference_date, 4, 18, 0, now)  # Friday 18:00
        next_biweekly2 = get_next_biweekly_event_time(reference_date_2, 0, 12, 0, now)  # Monday 12:00
        
        time_to_biweekly1 = next_biweekly1 - now
        time_to_biweekly2 = next_biweekly2 - now
        
        embed.add_field(
            name="🌟 Biweekly Event 1 (Every other Friday 18:00)",
            value=f"Next: <t:{int(next_biweekly1.timestamp())}:F>\nIn: **{format_time_remaining(time_to_biweekly1)}**",
            inline=False
        )
        embed.add_field(
            name="👑 Biweekly Event 2 (Every other Monday 12:00)",
            value=f"Next: <t:{int(next_biweekly2.timestamp())}:F>\nIn: **{format_time_remaining(time_to_biweekly2)}**",
            inline=False
        )
    
    if not (ENABLE_48H_EVENTS or ENABLE_WEEKLY_EVENTS or ENABLE_BIWEEKLY_EVENTS):
        embed.description = "No events are currently enabled."
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="next", description="Show the next upcoming event")
async def next_event(interaction: discord.Interaction):
    """Display only the next event"""
    now = datetime.now(UTC)
    
    next_events = []
    
    # Collect all next events
    if ENABLE_48H_EVENTS:
        next_bear1 = get_next_48h_event_time(EVENT_48H_1_START, now)
        next_bear2 = get_next_48h_event_time(EVENT_48H_2_START, now)
        next_events.append(("🔥 Bear 1", next_bear1))
        next_events.append(("🔥 Bear 2", next_bear2))
    
    if ENABLE_WEEKLY_EVENTS:
        next_weekly1 = get_next_weekly_event_time(6, 14, 0, now)
        next_weekly2 = get_next_weekly_event_time(2, 20, 0, now)
        next_events.append(("⚔️ Weekly Event 1", next_weekly1))
        next_events.append(("🎯 Weekly Event 2", next_weekly2))
    
    if ENABLE_BIWEEKLY_EVENTS:
        reference_date = datetime(2025, 1, 3, 18, 0, 0)
        reference_date_2 = datetime(2025, 1, 6, 12, 0, 0)
        next_biweekly1 = get_next_biweekly_event_time(reference_date, 4, 18, 0, now)
        next_biweekly2 = get_next_biweekly_event_time(reference_date_2, 0, 12, 0, now)
        next_events.append(("🌟 Biweekly Event 1", next_biweekly1))
        next_events.append(("👑 Biweekly Event 2", next_biweekly2))
    
    if not next_events:
        await interaction.response.send_message("No events are currently enabled.")
        return
    
    # Find the soonest event
    next_events.sort(key=lambda x: x[1])
    event_name, event_time = next_events[0]
    
    time_remaining = event_time - now
    
    embed = discord.Embed(
        title="⏱️ Next Event",
        description=f"**{event_name}**",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Scheduled Time",
        value=f"<t:{int(event_time.timestamp())}:F>",
        inline=False
    )
    embed.add_field(
        name="Time Remaining",
        value=f"**{format_time_remaining(time_remaining)}**",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
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
    
    # Sync slash commands
    await tree.sync()
    print(f"\nSlash commands synced! Use /events or /next")
    
    scheduler.start()

bot.run(TOKEN)

