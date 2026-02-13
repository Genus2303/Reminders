import discord
from discord.ext import tasks
import os
import asyncio
from datetime import datetime, timedelta
import pytz

# === ENABLE/DISABLE EVENTS ===
ENABLE_48H_EVENTS = True
ENABLE_WEEKLY_EVENTS = False
ENABLE_BIWEEKLY_EVENTS = True
ENABLE_4WEEKLY_EVENTS = True
ENABLE_TEST_ALERT = False  # Set to True to enable test alerts every 5 minutes

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GUILD_ID = os.getenv("GUILD_ID")  # Optional: Set your server ID for instant command sync

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

UTC = pytz.UTC

# ====================================================================
# === EVENT CONFIGURATION - EDIT THIS SECTION FOR ALL YOUR EVENTS ===
# ====================================================================

# 48-HOUR EVENTS
EVENT_48H_1_NAME = "🐻 Bear 1"
EVENT_48H_1_START = datetime(2026, 2, 13, 11, 20, 0)
EVENT_48H_1_MESSAGE = "@everyone 🐻 Bear 1 starts in 10 minutes!"

EVENT_48H_2_NAME = "🐻 Bear 2"
EVENT_48H_2_START = datetime(2026, 2, 13, 19, 50, 0)
EVENT_48H_2_MESSAGE = "@everyone 🐻 Bear 2 starts in 10 minutes!"

# WEEKLY EVENTS
WEEKLY_1_NAME = "⚔️ Weekly Event 1"
WEEKLY_1_DAY = 6  # 0=Monday, 6=Sunday
WEEKLY_1_HOUR = 14
WEEKLY_1_MINUTE = 0
WEEKLY_1_MESSAGE = "@everyone ⚔️ Weekly Event 1 starts now!"

WEEKLY_2_NAME = "🎯 Weekly Event 2"
WEEKLY_2_DAY = 2  # Wednesday
WEEKLY_2_HOUR = 20
WEEKLY_2_MINUTE = 0
WEEKLY_2_MESSAGE = "@everyone 🎯 Weekly Event 2 starts now!"

# BIWEEKLY EVENTS
BIWEEKLY_1_NAME = "⚔️ Foundry legion 2"
BIWEEKLY_1_REFERENCE = datetime(2026, 2, 8, 11, 50, 0)
BIWEEKLY_1_DAY = 6  # Sunday
BIWEEKLY_1_HOUR = 11
BIWEEKLY_1_MINUTE = 50
BIWEEKLY_1_MESSAGE = "@everyone ⚔️ Foundry legion 2 starts in 10 minutes!"

BIWEEKLY_2_NAME = "⚔️ Foundry legion 1"
BIWEEKLY_2_REFERENCE = datetime(2026, 2, 8, 19, 50, 0)
BIWEEKLY_2_DAY = 6  # Sunday
BIWEEKLY_2_HOUR = 19
BIWEEKLY_2_MINUTE = 50
BIWEEKLY_2_MESSAGE = "@everyone ⚔️ Foundry legion 1 starts in 10 minutes!"

BIWEEKLY_3_NAME = "😈 Crazy Joe (Tuesday)"
BIWEEKLY_3_REFERENCE = datetime(2026, 1, 27, 11, 50, 0)
BIWEEKLY_3_DAY = 1  # Tuesday
BIWEEKLY_3_HOUR = 11
BIWEEKLY_3_MINUTE = 50
BIWEEKLY_3_MESSAGE = "@everyone 😈 Crazy Joe starts in 10 minutes!"

BIWEEKLY_4_NAME = "😈 Crazy Joe (Thursday)"
BIWEEKLY_4_REFERENCE = datetime(2026, 1, 29, 19, 50, 0)
BIWEEKLY_4_DAY = 3  # Thursday
BIWEEKLY_4_HOUR = 19
BIWEEKLY_4_MINUTE = 50
BIWEEKLY_4_MESSAGE = "@everyone 😈 Crazy Joe starts in 10 minutes!"

# 4-WEEKLY EVENTS
FOURWEEKLY_1_NAME = "✈️ Canyon legion 1"
FOURWEEKLY_1_REFERENCE = datetime(2026, 1, 24, 11, 50, 0)
FOURWEEKLY_1_DAY = 5  # Saturday
FOURWEEKLY_1_HOUR = 11
FOURWEEKLY_1_MINUTE = 50
FOURWEEKLY_1_MESSAGE = "@everyone ✈️ Canyon legion 1 starts in 10 minutes!"

FOURWEEKLY_2_NAME = "✈️ Canyon legion 2"
FOURWEEKLY_2_REFERENCE = datetime(2026, 1, 24, 19, 50, 0)
FOURWEEKLY_2_DAY = 5  # Saturday
FOURWEEKLY_2_HOUR = 19
FOURWEEKLY_2_MINUTE = 50
FOURWEEKLY_2_MESSAGE = "@everyone ✈️ Canyon legion 2 starts in 10 minutes!"

# ====================================================================
# === END OF EVENT CONFIGURATION ===
# ====================================================================

# === TRACK LAST RUN TIMES ===
last_run = {
    '48h_event_1': None,
    '48h_event_2': None,
    'weekly_event_1': None,
    'weekly_event_2': None,
    'biweekly_event_1': None,
    'biweekly_event_2': None,
    'biweekly_event_3': None,
    'biweekly_event_4': None,
    '4weekly_event_1': None,
    '4weekly_event_2': None,
    'test_alert': None
}

async def send_message(message):
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(message)

def should_run_event(event_key, now, cooldown_minutes=55):
    """
    Check if enough time has passed since the last run of this event.
    Uses a cooldown to prevent duplicate triggers.
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
    
    if time_diff.total_seconds() < 0:
        return start_date
    
    hours_since_start = time_diff.total_seconds() / 3600
    intervals_passed = int(hours_since_start / 48)
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
    
    if next_time <= now:
        next_time += timedelta(days=7)
    
    return next_time

def get_next_biweekly_event_time(reference_date, target_weekday, target_hour, target_minute, now):
    """Calculate the next occurrence of a biweekly event"""
    if reference_date.tzinfo is None:
        reference_date = UTC.localize(reference_date)
    
    current_weekday = now.weekday()
    days_until = (target_weekday - current_weekday) % 7
    
    candidate_date = now.date() + timedelta(days=days_until)
    candidate_time = datetime.combine(candidate_date, datetime.min.time()).replace(
        hour=target_hour, minute=target_minute, tzinfo=UTC
    )
    
    if candidate_time <= now:
        candidate_time += timedelta(days=7)
        candidate_date = candidate_time.date()
    
    days_diff = (candidate_date - reference_date.date()).days
    weeks_diff = days_diff // 7
    
    if weeks_diff % 2 != 0:
        candidate_time += timedelta(days=7)
    
    return candidate_time

def get_next_4weekly_event_time(reference_date, target_weekday, target_hour, target_minute, now):
    """Calculate the next occurrence of a 4-weekly event"""
    if reference_date.tzinfo is None:
        reference_date = UTC.localize(reference_date)
    
    current_weekday = now.weekday()
    days_until = (target_weekday - current_weekday) % 7
    
    candidate_date = now.date() + timedelta(days=days_until)
    candidate_time = datetime.combine(candidate_date, datetime.min.time()).replace(
        hour=target_hour, minute=target_minute, tzinfo=UTC
    )
    
    if candidate_time <= now:
        candidate_time += timedelta(days=7)
        candidate_date = candidate_time.date()
    
    days_diff = (candidate_date - reference_date.date()).days
    weeks_diff = days_diff // 7
    
    while weeks_diff % 4 != 0:
        candidate_time += timedelta(days=7)
        candidate_date = candidate_time.date()
        days_diff = (candidate_date - reference_date.date()).days
        weeks_diff = days_diff // 7
    
    return candidate_time

def should_trigger_48h_event(start_date, now):
    """Check if a 48-hour interval event should trigger (with 2-minute window)"""
    if start_date.tzinfo is None:
        start_date = UTC.localize(start_date)
    
    time_diff = now - start_date
    
    if time_diff.total_seconds() < 0:
        return False
    
    hours_since_start = time_diff.total_seconds() / 3600
    intervals_passed = hours_since_start / 48
    
    interval_number = round(intervals_passed)
    expected_time = start_date + timedelta(hours=interval_number * 48)
    
    # Allow 2-minute window (1 minute before and 1 minute after)
    if now.hour == expected_time.hour and abs(now.minute - expected_time.minute) <= 1:
        if abs(intervals_passed - interval_number) < (2/60):  # Within 2 minutes
            return True
    
    return False

def is_time_match(now, target_hour, target_minute):
    """Check if current time matches target time (with 1-minute window)"""
    return now.hour == target_hour and abs(now.minute - target_minute) <= 1

@tasks.loop(minutes=1)
async def scheduler():
    now = datetime.now(UTC)
    
    # === TEST ALERT ===
    if ENABLE_TEST_ALERT:
        if now.minute % 5 == 0 and should_run_event('test_alert', now, cooldown_minutes=4):
            await send_message("🧪 **TEST ALERT** - Bot is running! Current time: " + now.strftime("%H:%M UTC"))
            mark_event_run('test_alert', now)
    
    # === 48-HOUR INTERVAL EVENTS ===
    if ENABLE_48H_EVENTS:
        if should_trigger_48h_event(EVENT_48H_1_START, now) and should_run_event('48h_event_1', now, cooldown_minutes=2880):
            await send_message(EVENT_48H_1_MESSAGE)
            mark_event_run('48h_event_1', now)
        
        if should_trigger_48h_event(EVENT_48H_2_START, now) and should_run_event('48h_event_2', now, cooldown_minutes=2880):
            await send_message(EVENT_48H_2_MESSAGE)
            mark_event_run('48h_event_2', now)
    
    # === WEEKLY EVENTS ===
    if ENABLE_WEEKLY_EVENTS:
        if now.weekday() == WEEKLY_1_DAY and is_time_match(now, WEEKLY_1_HOUR, WEEKLY_1_MINUTE) and should_run_event('weekly_event_1', now, cooldown_minutes=10000):
            await send_message(WEEKLY_1_MESSAGE)
            mark_event_run('weekly_event_1', now)
        
        if now.weekday() == WEEKLY_2_DAY and is_time_match(now, WEEKLY_2_HOUR, WEEKLY_2_MINUTE) and should_run_event('weekly_event_2', now, cooldown_minutes=10000):
            await send_message(WEEKLY_2_MESSAGE)
            mark_event_run('weekly_event_2', now)
    
    # === BIWEEKLY EVENTS ===
    if ENABLE_BIWEEKLY_EVENTS:
        if now.weekday() == BIWEEKLY_1_DAY and is_time_match(now, BIWEEKLY_1_HOUR, BIWEEKLY_1_MINUTE):
            days_diff = (now.date() - BIWEEKLY_1_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0 and should_run_event('biweekly_event_1', now, cooldown_minutes=20000):
                await send_message(BIWEEKLY_1_MESSAGE)
                mark_event_run('biweekly_event_1', now)
        
        if now.weekday() == BIWEEKLY_2_DAY and is_time_match(now, BIWEEKLY_2_HOUR, BIWEEKLY_2_MINUTE):
            days_diff = (now.date() - BIWEEKLY_2_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0 and should_run_event('biweekly_event_2', now, cooldown_minutes=20000):
                await send_message(BIWEEKLY_2_MESSAGE)
                mark_event_run('biweekly_event_2', now)
        
        if now.weekday() == BIWEEKLY_3_DAY and is_time_match(now, BIWEEKLY_3_HOUR, BIWEEKLY_3_MINUTE):
            days_diff = (now.date() - BIWEEKLY_3_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0 and should_run_event('biweekly_event_3', now, cooldown_minutes=20000):
                await send_message(BIWEEKLY_3_MESSAGE)
                mark_event_run('biweekly_event_3', now)
        
        if now.weekday() == BIWEEKLY_4_DAY and is_time_match(now, BIWEEKLY_4_HOUR, BIWEEKLY_4_MINUTE):
            days_diff = (now.date() - BIWEEKLY_4_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0 and should_run_event('biweekly_event_4', now, cooldown_minutes=20000):
                await send_message(BIWEEKLY_4_MESSAGE)
                mark_event_run('biweekly_event_4', now)
    
    # === 4-WEEKLY EVENTS ===
    if ENABLE_4WEEKLY_EVENTS:
        if now.weekday() == FOURWEEKLY_1_DAY and is_time_match(now, FOURWEEKLY_1_HOUR, FOURWEEKLY_1_MINUTE):
            days_diff = (now.date() - FOURWEEKLY_1_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 4 == 0 and should_run_event('4weekly_event_1', now, cooldown_minutes=40000):
                await send_message(FOURWEEKLY_1_MESSAGE)
                mark_event_run('4weekly_event_1', now)
        
        if now.weekday() == FOURWEEKLY_2_DAY and is_time_match(now, FOURWEEKLY_2_HOUR, FOURWEEKLY_2_MINUTE):
            days_diff = (now.date() - FOURWEEKLY_2_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 4 == 0 and should_run_event('4weekly_event_2', now, cooldown_minutes=40000):
                await send_message(FOURWEEKLY_2_MESSAGE)
                mark_event_run('4weekly_event_2', now)

@tree.command(name="events", description="Show when all events are scheduled")
async def show_events(interaction: discord.Interaction):
    """Display all upcoming events with countdowns"""
    now = datetime.now(UTC)
    
    embed = discord.Embed(
        title="📅 SEA Events Schedule 💜",
        description="Times are local",
        color=discord.Color.blue()
    )
    
    if ENABLE_48H_EVENTS:
        next_bear1 = get_next_48h_event_time(EVENT_48H_1_START, now)
        next_bear2 = get_next_48h_event_time(EVENT_48H_2_START, now)
        
        embed.add_field(
            name=f"{EVENT_48H_1_NAME} (Every 48 hours)",
            value=f"Next: <t:{int(next_bear1.timestamp())}:F>\nIn: **{format_time_remaining(next_bear1 - now)}**",
            inline=False
        )
        embed.add_field(
            name=f"{EVENT_48H_2_NAME} (Every 48 hours)",
            value=f"Next: <t:{int(next_bear2.timestamp())}:F>\nIn: **{format_time_remaining(next_bear2 - now)}**",
            inline=False
        )
    
    if ENABLE_WEEKLY_EVENTS:
        next_weekly1 = get_next_weekly_event_time(WEEKLY_1_DAY, WEEKLY_1_HOUR, WEEKLY_1_MINUTE, now)
        next_weekly2 = get_next_weekly_event_time(WEEKLY_2_DAY, WEEKLY_2_HOUR, WEEKLY_2_MINUTE, now)
        
        embed.add_field(
            name=WEEKLY_1_NAME,
            value=f"Next: <t:{int(next_weekly1.timestamp())}:F>\nIn: **{format_time_remaining(next_weekly1 - now)}**",
            inline=False
        )
        embed.add_field(
            name=WEEKLY_2_NAME,
            value=f"Next: <t:{int(next_weekly2.timestamp())}:F>\nIn: **{format_time_remaining(next_weekly2 - now)}**",
            inline=False
        )
    
    if ENABLE_BIWEEKLY_EVENTS:
        next_biweekly1 = get_next_biweekly_event_time(BIWEEKLY_1_REFERENCE, BIWEEKLY_1_DAY, BIWEEKLY_1_HOUR, BIWEEKLY_1_MINUTE, now)
        next_biweekly2 = get_next_biweekly_event_time(BIWEEKLY_2_REFERENCE, BIWEEKLY_2_DAY, BIWEEKLY_2_HOUR, BIWEEKLY_2_MINUTE, now)
        next_biweekly3 = get_next_biweekly_event_time(BIWEEKLY_3_REFERENCE, BIWEEKLY_3_DAY, BIWEEKLY_3_HOUR, BIWEEKLY_3_MINUTE, now)
        next_biweekly4 = get_next_biweekly_event_time(BIWEEKLY_4_REFERENCE, BIWEEKLY_4_DAY, BIWEEKLY_4_HOUR, BIWEEKLY_4_MINUTE, now)
        
        embed.add_field(
            name=BIWEEKLY_1_NAME,
            value=f"Next: <t:{int(next_biweekly1.timestamp())}:F>\nIn: **{format_time_remaining(next_biweekly1 - now)}**",
            inline=False
        )
        embed.add_field(
            name=BIWEEKLY_2_NAME,
            value=f"Next: <t:{int(next_biweekly2.timestamp())}:F>\nIn: **{format_time_remaining(next_biweekly2 - now)}**",
            inline=False
        )
        embed.add_field(
            name=BIWEEKLY_3_NAME,
            value=f"Next: <t:{int(next_biweekly3.timestamp())}:F>\nIn: **{format_time_remaining(next_biweekly3 - now)}**",
            inline=False
        )
        embed.add_field(
            name=BIWEEKLY_4_NAME,
            value=f"Next: <t:{int(next_biweekly4.timestamp())}:F>\nIn: **{format_time_remaining(next_biweekly4 - now)}**",
            inline=False
        )
    
    if ENABLE_4WEEKLY_EVENTS:
        next_4weekly1 = get_next_4weekly_event_time(FOURWEEKLY_1_REFERENCE, FOURWEEKLY_1_DAY, FOURWEEKLY_1_HOUR, FOURWEEKLY_1_MINUTE, now)
        next_4weekly2 = get_next_4weekly_event_time(FOURWEEKLY_2_REFERENCE, FOURWEEKLY_2_DAY, FOURWEEKLY_2_HOUR, FOURWEEKLY_2_MINUTE, now)
        
        embed.add_field(
            name=FOURWEEKLY_1_NAME,
            value=f"Next: <t:{int(next_4weekly1.timestamp())}:F>\nIn: **{format_time_remaining(next_4weekly1 - now)}**",
            inline=False
        )
        embed.add_field(
            name=FOURWEEKLY_2_NAME,
            value=f"Next: <t:{int(next_4weekly2.timestamp())}:F>\nIn: **{format_time_remaining(next_4weekly2 - now)}**",
            inline=False
        )
    
    if not (ENABLE_48H_EVENTS or ENABLE_WEEKLY_EVENTS or ENABLE_BIWEEKLY_EVENTS or ENABLE_4WEEKLY_EVENTS):
        embed.description = "No events are currently enabled."
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="next", description="Show the next upcoming event")
async def next_event(interaction: discord.Interaction):
    """Display only the next event"""
    now = datetime.now(UTC)
    
    next_events = []
    
    if ENABLE_48H_EVENTS:
        next_events.append((EVENT_48H_1_NAME, get_next_48h_event_time(EVENT_48H_1_START, now)))
        next_events.append((EVENT_48H_2_NAME, get_next_48h_event_time(EVENT_48H_2_START, now)))
    
    if ENABLE_WEEKLY_EVENTS:
        next_events.append((WEEKLY_1_NAME, get_next_weekly_event_time(WEEKLY_1_DAY, WEEKLY_1_HOUR, WEEKLY_1_MINUTE, now)))
        next_events.append((WEEKLY_2_NAME, get_next_weekly_event_time(WEEKLY_2_DAY, WEEKLY_2_HOUR, WEEKLY_2_MINUTE, now)))
    
    if ENABLE_BIWEEKLY_EVENTS:
        next_events.append((BIWEEKLY_1_NAME, get_next_biweekly_event_time(BIWEEKLY_1_REFERENCE, BIWEEKLY_1_DAY, BIWEEKLY_1_HOUR, BIWEEKLY_1_MINUTE, now)))
        next_events.append((BIWEEKLY_2_NAME, get_next_biweekly_event_time(BIWEEKLY_2_REFERENCE, BIWEEKLY_2_DAY, BIWEEKLY_2_HOUR, BIWEEKLY_2_MINUTE, now)))
        next_events.append((BIWEEKLY_3_NAME, get_next_biweekly_event_time(BIWEEKLY_3_REFERENCE, BIWEEKLY_3_DAY, BIWEEKLY_3_HOUR, BIWEEKLY_3_MINUTE, now)))
        next_events.append((BIWEEKLY_4_NAME, get_next_biweekly_event_time(BIWEEKLY_4_REFERENCE, BIWEEKLY_4_DAY, BIWEEKLY_4_HOUR, BIWEEKLY_4_MINUTE, now)))
    
    if ENABLE_4WEEKLY_EVENTS:
        next_events.append((FOURWEEKLY_1_NAME, get_next_4weekly_event_time(FOURWEEKLY_1_REFERENCE, FOURWEEKLY_1_DAY, FOURWEEKLY_1_HOUR, FOURWEEKLY_1_MINUTE, now)))
        next_events.append((FOURWEEKLY_2_NAME, get_next_4weekly_event_time(FOURWEEKLY_2_REFERENCE, FOURWEEKLY_2_DAY, FOURWEEKLY_2_HOUR, FOURWEEKLY_2_MINUTE, now)))
    
    if not next_events:
        await interaction.response.send_message("No events are currently enabled.")
        return
    
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

@tree.command(name="test", description="Send a test notification to verify the bot is working")
async def test_notification(interaction: discord.Interaction):
    """Send a test notification"""
    now = datetime.now(UTC)
    
    # Send response to user first
    await interaction.response.send_message("✅ Sending test notification...", ephemeral=True)
    
    # Send test message to the channel
    await send_message(f"🧪 **TEST NOTIFICATION**\nBot is working correctly!\nCurrent time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\nTriggered by: {interaction.user.mention}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot is monitoring events in channel ID: {CHANNEL_ID}")
    print(f"\nScheduled Events (all times in UTC):")
    print(f"  Test Alert: {'ENABLED (every 5 minutes)' if ENABLE_TEST_ALERT else 'DISABLED'}")
    print(f"  48h Events: {'ENABLED' if ENABLE_48H_EVENTS else 'DISABLED'}")
    if ENABLE_48H_EVENTS:
        print(f"    - {EVENT_48H_1_NAME}: Every 48 hours starting {EVENT_48H_1_START}")
        print(f"    - {EVENT_48H_2_NAME}: Every 48 hours starting {EVENT_48H_2_START}")
    print(f"  Weekly Events: {'ENABLED' if ENABLE_WEEKLY_EVENTS else 'DISABLED'}")
    print(f"  Biweekly Events: {'ENABLED' if ENABLE_BIWEEKLY_EVENTS else 'DISABLED'}")
    print(f"  4-Weekly Events: {'ENABLED' if ENABLE_4WEEKLY_EVENTS else 'DISABLED'}")
    
    # Sync commands - use guild sync if GUILD_ID is set for instant updates
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
        print(f"\n✅ Slash commands synced to guild {GUILD_ID} (instant)")
    else:
        await tree.sync()
        print(f"\n⏳ Slash commands synced globally (may take up to 1 hour)")
    
    print(f"\nAvailable commands:")
    print(f"  /events - Show all upcoming events")
    print(f"  /next - Show the next event")
    print(f"  /test - Send a test notification")
    
    scheduler.start()

bot.run(TOKEN)
