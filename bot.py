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
ENABLE_DAILY_SUMMARY = True  # Set to True to send daily event summary at 00:00 UTC

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
    'test_alert': None,
    'daily_summary': None
}

# === CUSTOM ONE-TIME ALERTS ===
custom_alerts = []  # List of tuples: (datetime, name, message)

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

def get_todays_events(now):
    """Get all events scheduled for today with their times and finished status"""
    today = now.date()
    today_events = []
    
    # Check 48-hour events
    if ENABLE_48H_EVENTS:
        next_bear1 = get_next_48h_event_time(EVENT_48H_1_START, now)
        if next_bear1.date() == today:
            today_events.append((next_bear1, EVENT_48H_1_NAME, next_bear1 < now))
        
        prev_bear1 = next_bear1 - timedelta(hours=48)
        if prev_bear1.date() == today:
            today_events.append((prev_bear1, EVENT_48H_1_NAME, prev_bear1 < now))
        
        next_bear2 = get_next_48h_event_time(EVENT_48H_2_START, now)
        if next_bear2.date() == today:
            today_events.append((next_bear2, EVENT_48H_2_NAME, next_bear2 < now))
        
        prev_bear2 = next_bear2 - timedelta(hours=48)
        if prev_bear2.date() == today:
            today_events.append((prev_bear2, EVENT_48H_2_NAME, prev_bear2 < now))
    
    # Check weekly events
    if ENABLE_WEEKLY_EVENTS:
        if now.weekday() == WEEKLY_1_DAY:
            event_time = datetime.combine(today, datetime.min.time()).replace(
                hour=WEEKLY_1_HOUR, minute=WEEKLY_1_MINUTE, tzinfo=UTC
            )
            today_events.append((event_time, WEEKLY_1_NAME, event_time < now))
        
        if now.weekday() == WEEKLY_2_DAY:
            event_time = datetime.combine(today, datetime.min.time()).replace(
                hour=WEEKLY_2_HOUR, minute=WEEKLY_2_MINUTE, tzinfo=UTC
            )
            today_events.append((event_time, WEEKLY_2_NAME, event_time < now))
    
    # Check biweekly events
    if ENABLE_BIWEEKLY_EVENTS:
        if now.weekday() == BIWEEKLY_1_DAY:
            days_diff = (today - BIWEEKLY_1_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0:
                event_time = datetime.combine(today, datetime.min.time()).replace(
                    hour=BIWEEKLY_1_HOUR, minute=BIWEEKLY_1_MINUTE, tzinfo=UTC
                )
                today_events.append((event_time, BIWEEKLY_1_NAME, event_time < now))
        
        if now.weekday() == BIWEEKLY_2_DAY:
            days_diff = (today - BIWEEKLY_2_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0:
                event_time = datetime.combine(today, datetime.min.time()).replace(
                    hour=BIWEEKLY_2_HOUR, minute=BIWEEKLY_2_MINUTE, tzinfo=UTC
                )
                today_events.append((event_time, BIWEEKLY_2_NAME, event_time < now))
        
        if now.weekday() == BIWEEKLY_3_DAY:
            days_diff = (today - BIWEEKLY_3_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0:
                event_time = datetime.combine(today, datetime.min.time()).replace(
                    hour=BIWEEKLY_3_HOUR, minute=BIWEEKLY_3_MINUTE, tzinfo=UTC
                )
                today_events.append((event_time, BIWEEKLY_3_NAME, event_time < now))
        
        if now.weekday() == BIWEEKLY_4_DAY:
            days_diff = (today - BIWEEKLY_4_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0:
                event_time = datetime.combine(today, datetime.min.time()).replace(
                    hour=BIWEEKLY_4_HOUR, minute=BIWEEKLY_4_MINUTE, tzinfo=UTC
                )
                today_events.append((event_time, BIWEEKLY_4_NAME, event_time < now))
    
    # Check 4-weekly events
    if ENABLE_4WEEKLY_EVENTS:
        if now.weekday() == FOURWEEKLY_1_DAY:
            days_diff = (today - FOURWEEKLY_1_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 4 == 0:
                event_time = datetime.combine(today, datetime.min.time()).replace(
                    hour=FOURWEEKLY_1_HOUR, minute=FOURWEEKLY_1_MINUTE, tzinfo=UTC
                )
                today_events.append((event_time, FOURWEEKLY_1_NAME, event_time < now))
        
        if now.weekday() == FOURWEEKLY_2_DAY:
            days_diff = (today - FOURWEEKLY_2_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 4 == 0:
                event_time = datetime.combine(today, datetime.min.time()).replace(
                    hour=FOURWEEKLY_2_HOUR, minute=FOURWEEKLY_2_MINUTE, tzinfo=UTC
                )
                today_events.append((event_time, FOURWEEKLY_2_NAME, event_time < now))
    
    # Check custom alerts
    for alert_time, name, message in custom_alerts:
        if alert_time.date() == today:
            today_events.append((alert_time, f"🔔 {name}", alert_time < now))
    
    # Sort by time
    today_events.sort(key=lambda x: x[0])
    
    return today_events

@tasks.loop(minutes=1)
async def scheduler():
    now = datetime.now(UTC)
    
    # === DAILY SUMMARY at 00:00 UTC ===
    if ENABLE_DAILY_SUMMARY:
        if now.hour == 0 and now.minute == 0 and should_run_event('daily_summary', now, cooldown_minutes=1400):  # ~23 hours
            today_events = get_todays_events(now)
            
            if today_events:
                message = f"📅 **TODAY'S EVENTS** - {now.strftime('%A, %B %d, %Y')}\n\n"
                
                for event_time, event_name, _ in today_events:
                    time_str = event_time.strftime('%H:%M UTC')
                    message += f"• **{time_str}** - {event_name}\n"
                
                message += f"\n{len(today_events)} event(s) scheduled today! 🎯"
                await send_message(message)
            else:
                await send_message(f"📅 **TODAY'S EVENTS** - {now.strftime('%A, %B %d, %Y')}\n\nNo events scheduled for today. Enjoy your day! ☀️")
            
            mark_event_run('daily_summary', now)
    
    # === CUSTOM ONE-TIME ALERTS ===
    global custom_alerts
    triggered_alerts = []
    for alert_time, name, message in custom_alerts:
        # Check if it's time for this alert (with 1-minute window)
        if is_time_match(now, alert_time.hour, alert_time.minute) and now.date() == alert_time.date():
            await send_message(message)
            triggered_alerts.append((alert_time, name, message))
    
    # Remove triggered alerts
    for alert in triggered_alerts:
        custom_alerts.remove(alert)
    
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
    """Display all upcoming events with countdowns, sorted by time"""
    now = datetime.now(UTC)
    
    # Collect all events with their next occurrence time
    all_events = []
    
    if ENABLE_48H_EVENTS:
        next_bear1 = get_next_48h_event_time(EVENT_48H_1_START, now)
        next_bear2 = get_next_48h_event_time(EVENT_48H_2_START, now)
        all_events.append((next_bear1, EVENT_48H_1_NAME + " (Every 48 hours)", next_bear1))
        all_events.append((next_bear2, EVENT_48H_2_NAME + " (Every 48 hours)", next_bear2))
    
    if ENABLE_WEEKLY_EVENTS:
        next_weekly1 = get_next_weekly_event_time(WEEKLY_1_DAY, WEEKLY_1_HOUR, WEEKLY_1_MINUTE, now)
        next_weekly2 = get_next_weekly_event_time(WEEKLY_2_DAY, WEEKLY_2_HOUR, WEEKLY_2_MINUTE, now)
        all_events.append((next_weekly1, WEEKLY_1_NAME, next_weekly1))
        all_events.append((next_weekly2, WEEKLY_2_NAME, next_weekly2))
    
    if ENABLE_BIWEEKLY_EVENTS:
        next_biweekly1 = get_next_biweekly_event_time(BIWEEKLY_1_REFERENCE, BIWEEKLY_1_DAY, BIWEEKLY_1_HOUR, BIWEEKLY_1_MINUTE, now)
        next_biweekly2 = get_next_biweekly_event_time(BIWEEKLY_2_REFERENCE, BIWEEKLY_2_DAY, BIWEEKLY_2_HOUR, BIWEEKLY_2_MINUTE, now)
        next_biweekly3 = get_next_biweekly_event_time(BIWEEKLY_3_REFERENCE, BIWEEKLY_3_DAY, BIWEEKLY_3_HOUR, BIWEEKLY_3_MINUTE, now)
        next_biweekly4 = get_next_biweekly_event_time(BIWEEKLY_4_REFERENCE, BIWEEKLY_4_DAY, BIWEEKLY_4_HOUR, BIWEEKLY_4_MINUTE, now)
        all_events.append((next_biweekly1, BIWEEKLY_1_NAME, next_biweekly1))
        all_events.append((next_biweekly2, BIWEEKLY_2_NAME, next_biweekly2))
        all_events.append((next_biweekly3, BIWEEKLY_3_NAME, next_biweekly3))
        all_events.append((next_biweekly4, BIWEEKLY_4_NAME, next_biweekly4))
    
    if ENABLE_4WEEKLY_EVENTS:
        next_4weekly1 = get_next_4weekly_event_time(FOURWEEKLY_1_REFERENCE, FOURWEEKLY_1_DAY, FOURWEEKLY_1_HOUR, FOURWEEKLY_1_MINUTE, now)
        next_4weekly2 = get_next_4weekly_event_time(FOURWEEKLY_2_REFERENCE, FOURWEEKLY_2_DAY, FOURWEEKLY_2_HOUR, FOURWEEKLY_2_MINUTE, now)
        all_events.append((next_4weekly1, FOURWEEKLY_1_NAME, next_4weekly1))
        all_events.append((next_4weekly2, FOURWEEKLY_2_NAME, next_4weekly2))
    
    # Add custom alerts
    for alert_time, name, message in custom_alerts:
        all_events.append((alert_time, f"🔔 {name}", alert_time))
    
    if not all_events:
        embed = discord.Embed(
            title="📅 SEA Events Schedule 💜",
            description="No events are currently enabled.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    # Sort by time (earliest first)
    all_events.sort(key=lambda x: x[0])
    
    embed = discord.Embed(
        title="📅 SEA Events Schedule 💜",
        description="Times are local • Sorted by next occurrence",
        color=discord.Color.blue()
    )
    
    for event_time, event_name, _ in all_events:
        time_remaining = event_time - now
        embed.add_field(
            name=event_name,
            value=f"Next: <t:{int(event_time.timestamp())}:F>\nIn: **{format_time_remaining(time_remaining)}**",
            inline=False
        )
    
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
    
    # Add custom alerts
    for alert_time, name, message in custom_alerts:
        next_events.append((f"🔔 {name}", alert_time))
    
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

@tree.command(name="toggle_test", description="Toggle automatic test alerts on/off")
async def toggle_test_alerts(interaction: discord.Interaction):
    """Toggle the automatic test alert feature"""
    global ENABLE_TEST_ALERT
    
    ENABLE_TEST_ALERT = not ENABLE_TEST_ALERT
    
    status = "✅ ENABLED" if ENABLE_TEST_ALERT else "❌ DISABLED"
    message = f"Test alerts are now **{status}**"
    
    if ENABLE_TEST_ALERT:
        message += "\n📢 The bot will send automatic test messages every 5 minutes."
    else:
        message += "\n🔇 Automatic test messages are disabled. Use `/test` for manual testing."
    
    await interaction.response.send_message(message, ephemeral=True)

@tree.command(name="help_scheduler", description="Show all available commands and event information")
async def help_scheduler(interaction: discord.Interaction):
    """Display help menu with all commands and event types"""
    
    embed = discord.Embed(
        title="📚 Event Scheduler Bot - Help Menu",
        description="Your comprehensive guide to event scheduling commands",
        color=discord.Color.purple()
    )
    
    # Commands section
    embed.add_field(
        name="📋 Available Commands",
        value=(
            "**`/events`** - View all scheduled events with countdowns\n"
            "**`/next`** - Show only the next upcoming event\n"
            "**`/today`** - Show all events happening today\n"
            "**`/test`** - Send a one-time test notification\n"
            "**`/toggle_test`** - Enable/disable automatic test alerts (every 5 min)\n"
            "**`/add`** - Add a custom one-time alert\n"
            "**`/list_custom`** - View all pending custom alerts\n"
            "**`/help_scheduler`** - Show this help menu"
        ),
        inline=False
    )
    
    # Event types section
    embed.add_field(
        name="🗓️ Event Types",
        value=(
            f"**48-Hour Events:** {len([x for x in [ENABLE_48H_EVENTS] if x])*2} events - Repeats every 2 days\n"
            f"**Weekly Events:** {len([x for x in [ENABLE_WEEKLY_EVENTS] if x])*2} events - Repeats every week\n"
            f"**Biweekly Events:** {len([x for x in [ENABLE_BIWEEKLY_EVENTS] if x])*4} events - Repeats every 2 weeks\n"
            f"**4-Weekly Events:** {len([x for x in [ENABLE_4WEEKLY_EVENTS] if x])*2} events - Repeats every 4 weeks\n"
            f"**Custom Alerts:** {len(custom_alerts)} pending - One-time notifications"
        ),
        inline=False
    )
    
    # Current status section
    status_text = []
    if ENABLE_48H_EVENTS:
        status_text.append("✅ 48-Hour Events")
    if ENABLE_WEEKLY_EVENTS:
        status_text.append("✅ Weekly Events")
    if ENABLE_BIWEEKLY_EVENTS:
        status_text.append("✅ Biweekly Events")
    if ENABLE_4WEEKLY_EVENTS:
        status_text.append("✅ 4-Weekly Events")
    if ENABLE_TEST_ALERT:
        status_text.append("✅ Auto Test Alerts")
    
    if not status_text:
        status_text.append("⚠️ No events currently enabled")
    
    embed.add_field(
        name="⚙️ Current Status",
        value="\n".join(status_text),
        inline=False
    )
    
    # Features section
    embed.add_field(
        name="✨ Features",
        value=(
            "• **Automatic Reminders** - Get notified before events start\n"
            "• **Timezone Support** - Times shown in your local timezone\n"
            "• **Countdown Timers** - See exactly when events begin\n"
            "• **Duplicate Prevention** - Smart cooldowns prevent spam\n"
            "• **Custom Alerts** - Add one-time notifications anytime"
        ),
        inline=False
    )
    
    # Footer
    embed.set_footer(text="All event times are in UTC • Bot checks every minute")
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="add", description="Add a custom one-time alert")
async def add_custom_alert(
    interaction: discord.Interaction,
    name: str,
    hour: int,
    minute: int,
    message: str,
    day: int = None,
    month: int = None,
    year: int = None
):
    """
    Add a custom one-time alert
    
    Parameters:
    name: Short name for the alert (e.g., "Boss Spawn", "Guild Meeting")
    hour: Hour in UTC (0-23)
    minute: Minute (0-59)
    message: The message to send
    day: Day of month (defaults to today if not specified)
    month: Month (defaults to current month if not specified)
    year: Year (defaults to current year if not specified)
    """
    global custom_alerts
    
    now = datetime.now(UTC)
    
    # Validate hour and minute
    if not (0 <= hour <= 23):
        await interaction.response.send_message("❌ Hour must be between 0 and 23", ephemeral=True)
        return
    
    if not (0 <= minute <= 59):
        await interaction.response.send_message("❌ Minute must be between 0 and 59", ephemeral=True)
        return
    
    # Use current date if not specified
    target_year = year if year is not None else now.year
    target_month = month if month is not None else now.month
    target_day = day if day is not None else now.day
    
    try:
        alert_time = datetime(target_year, target_month, target_day, hour, minute, 0, tzinfo=UTC)
    except ValueError as e:
        await interaction.response.send_message(f"❌ Invalid date: {e}", ephemeral=True)
        return
    
    # Check if the time is in the past
    if alert_time < now:
        await interaction.response.send_message(
            f"❌ Cannot set alert in the past!\nSpecified time: {alert_time.strftime('%Y-%m-%d %H:%M UTC')}\nCurrent time: {now.strftime('%Y-%m-%d %H:%M UTC')}",
            ephemeral=True
        )
        return
    
    # Add the alert
    custom_alerts.append((alert_time, name, message))
    custom_alerts.sort(key=lambda x: x[0])  # Keep sorted by time
    
    embed = discord.Embed(
        title="✅ Custom Alert Added",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Alert Name",
        value=f"🔔 {name}",
        inline=False
    )
    embed.add_field(
        name="Scheduled Time",
        value=f"<t:{int(alert_time.timestamp())}:F>",
        inline=False
    )
    embed.add_field(
        name="Time Until Alert",
        value=f"**{format_time_remaining(alert_time - now)}**",
        inline=False
    )
    embed.add_field(
        name="Message",
        value=message,
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="list_custom", description="View all pending custom alerts")
async def list_custom_alerts(interaction: discord.Interaction):
    """List all pending custom alerts"""
    
    if not custom_alerts:
        await interaction.response.send_message("📭 No custom alerts scheduled.", ephemeral=True)
        return
    
    now = datetime.now(UTC)
    
    embed = discord.Embed(
        title="📋 Pending Custom Alerts",
        description=f"{len(custom_alerts)} alert(s) scheduled",
        color=discord.Color.blue()
    )
    
    for i, (alert_time, name, message) in enumerate(custom_alerts[:10], 1):  # Show max 10
        time_remaining = alert_time - now
        message_preview = message[:100] + "..." if len(message) > 100 else message
        embed.add_field(
            name=f"#{i} - 🔔 {name}",
            value=f"**When:** <t:{int(alert_time.timestamp())}:R>\n**In:** {format_time_remaining(time_remaining)}\n**Message:** {message_preview}",
            inline=False
        )
    
    if len(custom_alerts) > 10:
        embed.set_footer(text=f"Showing 10 of {len(custom_alerts)} alerts")
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="today", description="Show all events scheduled for today")
async def today_events(interaction: discord.Interaction):
    """Display all events happening today, marking finished ones"""
    now = datetime.now(UTC)
    today = now.date()
    
    today_events_list = get_todays_events(now)
    
    if not today_events_list:
        embed = discord.Embed(
            title="📅 Today's Events",
            description=f"No events scheduled for {today.strftime('%A, %B %d, %Y')}",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    embed = discord.Embed(
        title="📅 Today's Events",
        description=f"{today.strftime('%A, %B %d, %Y')} • {len(today_events_list)} event(s)",
        color=discord.Color.blue()
    )
    
    for event_time, event_name, is_finished in today_events_list:
        status = "✅ Finished" if is_finished else f"⏰ In {format_time_remaining(event_time - now)}"
        time_str = event_time.strftime("%H:%M UTC")
        
        embed.add_field(
            name=f"{time_str} - {event_name}",
            value=status,
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot is monitoring events in channel ID: {CHANNEL_ID}")
    print(f"\nScheduled Events (all times in UTC):")
    print(f"  Daily Summary: {'ENABLED (00:00 UTC)' if ENABLE_DAILY_SUMMARY else 'DISABLED'}")
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
    print(f"  /today - Show all events for today")
    print(f"  /test - Send a test notification")
    print(f"  /toggle_test - Toggle automatic test alerts on/off")
    print(f"  /add - Add a custom one-time alert")
    print(f"  /list_custom - View pending custom alerts")
    print(f"  /help_scheduler - Show help menu with all commands")
    
    scheduler.start()

bot.run(TOKEN)

===================================================================
NOTE: This is the OLD bot. You need to make the changes listed in
COMPLETE_BOT_README.md to add the alert_before functionality.
===================================================================
