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
EVENT_48H_1_START = datetime(2026, 2, 13, 11, 30, 0)
EVENT_48H_1_ALERT_BEFORE = 10
EVENT_48H_1_MESSAGE = "@everyone 🐻 Bear 1 starts in {ALERT_MINUTES} minutes!"

EVENT_48H_2_NAME = "🐻 Bear 2"
EVENT_48H_2_START = datetime(2026, 2, 13, 20, 0, 0)
EVENT_48H_2_ALERT_BEFORE = 10
EVENT_48H_2_MESSAGE = "@everyone 🐻 Bear 2 starts in {ALERT_MINUTES} minutes!"

# WEEKLY EVENTS
WEEKLY_1_NAME = "⚔️ Weekly Event 1"
WEEKLY_1_DAY = 6  # 0=Monday, 6=Sunday
WEEKLY_1_HOUR = 14
WEEKLY_1_MINUTE = 0
WEEKLY_1_ALERT_BEFORE = 10
WEEKLY_1_MESSAGE = "@everyone ⚔️ Weekly Event 1 starts in {ALERT_MINUTES} minutes!"

WEEKLY_2_NAME = "🎯 Weekly Event 2"
WEEKLY_2_DAY = 2  # Wednesday
WEEKLY_2_HOUR = 20
WEEKLY_2_MINUTE = 0
WEEKLY_2_ALERT_BEFORE = 10
WEEKLY_2_MESSAGE = "@everyone 🎯 Weekly Event 2 starts in {ALERT_MINUTES} minutes!"

# BIWEEKLY EVENTS
BIWEEKLY_1_NAME = "⚔️ Foundry legion 2"
BIWEEKLY_1_REFERENCE = datetime(2026, 2, 8, 12, 0, 0)
BIWEEKLY_1_DAY = 6  # Sunday
BIWEEKLY_1_HOUR = 12
BIWEEKLY_1_MINUTE = 0
BIWEEKLY_1_ALERT_BEFORE = 10
BIWEEKLY_1_MESSAGE = "@everyone ⚔️ Foundry legion 2 starts in {ALERT_MINUTES} minutes!"

BIWEEKLY_2_NAME = "⚔️ Foundry legion 1"
BIWEEKLY_2_REFERENCE = datetime(2026, 2, 8, 20, 0, 0)
BIWEEKLY_2_DAY = 6  # Sunday
BIWEEKLY_2_HOUR = 20
BIWEEKLY_2_MINUTE = 0
BIWEEKLY_2_ALERT_BEFORE = 10
BIWEEKLY_2_MESSAGE = "@everyone ⚔️ Foundry legion 1 starts in {ALERT_MINUTES} minutes!"

BIWEEKLY_3_NAME = "😈 Crazy Joe (Tuesday)"
BIWEEKLY_3_REFERENCE = datetime(2026, 1, 27, 12, 0, 0)
BIWEEKLY_3_DAY = 1  # Tuesday
BIWEEKLY_3_HOUR = 12
BIWEEKLY_3_MINUTE = 0
BIWEEKLY_3_ALERT_BEFORE = 10
BIWEEKLY_3_MESSAGE = "@everyone 😈 Crazy Joe starts in {ALERT_MINUTES} minutes!"

BIWEEKLY_4_NAME = "😈 Crazy Joe (Thursday)"
BIWEEKLY_4_REFERENCE = datetime(2026, 1, 29, 20, 0, 0)
BIWEEKLY_4_DAY = 3  # Thursday
BIWEEKLY_4_HOUR = 20
BIWEEKLY_4_MINUTE = 0
BIWEEKLY_4_ALERT_BEFORE = 10
BIWEEKLY_4_MESSAGE = "@everyone 😈 Crazy Joe starts in {ALERT_MINUTES} minutes!"

# 4-WEEKLY EVENTS
FOURWEEKLY_1_NAME = "✈️ Canyon legion 1"
FOURWEEKLY_1_REFERENCE = datetime(2026, 1, 24, 12, 0, 0)
FOURWEEKLY_1_DAY = 5  # Saturday
FOURWEEKLY_1_HOUR = 12
FOURWEEKLY_1_MINUTE = 0
FOURWEEKLY_1_ALERT_BEFORE = 10
FOURWEEKLY_1_MESSAGE = "@everyone ✈️ Canyon legion 1 starts in {ALERT_MINUTES} minutes!"

FOURWEEKLY_2_NAME = "✈️ Canyon legion 2"
FOURWEEKLY_2_REFERENCE = datetime(2026, 1, 24, 20, 0, 0)
FOURWEEKLY_2_DAY = 5  # Saturday
FOURWEEKLY_2_HOUR = 20
FOURWEEKLY_2_MINUTE = 0
FOURWEEKLY_2_ALERT_BEFORE = 10
FOURWEEKLY_2_MESSAGE = "@everyone ✈️ Canyon legion 2 starts in {ALERT_MINUTES} minutes!"

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
custom_alerts = []  # List of tuples: (datetime, name, message, alert_before_minutes)

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
    for alert_time, name, message, alert_before in custom_alerts:
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
    for alert_time, name, message, alert_before in custom_alerts:
        alert_send_time = alert_time - timedelta(minutes=alert_before)
        if is_time_match(now, alert_send_time.hour, alert_send_time.minute) and now.date() == alert_send_time.date():
            final_message = message.replace("{ALERT_MINUTES}", str(alert_before))
            await send_message(final_message)
            triggered_alerts.append((alert_time, name, message, alert_before))
    
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
        next_48h_1 = get_next_48h_event_time(EVENT_48H_1_START, now)
        alert_time_48h_1 = next_48h_1 - timedelta(minutes=EVENT_48H_1_ALERT_BEFORE)
        if is_time_match(now, alert_time_48h_1.hour, alert_time_48h_1.minute) and now.date() == alert_time_48h_1.date() and should_run_event('48h_event_1', now, cooldown_minutes=2880):
            message = EVENT_48H_1_MESSAGE.replace("{ALERT_MINUTES}", str(EVENT_48H_1_ALERT_BEFORE))
            await send_message(message)
            mark_event_run('48h_event_1', now)
        
        next_48h_2 = get_next_48h_event_time(EVENT_48H_2_START, now)
        alert_time_48h_2 = next_48h_2 - timedelta(minutes=EVENT_48H_2_ALERT_BEFORE)
        if is_time_match(now, alert_time_48h_2.hour, alert_time_48h_2.minute) and now.date() == alert_time_48h_2.date() and should_run_event('48h_event_2', now, cooldown_minutes=2880):
            message = EVENT_48H_2_MESSAGE.replace("{ALERT_MINUTES}", str(EVENT_48H_2_ALERT_BEFORE))
            await send_message(message)
            mark_event_run('48h_event_2', now)
    
    # === WEEKLY EVENTS ===
    if ENABLE_WEEKLY_EVENTS:
        next_weekly1 = get_next_weekly_event_time(WEEKLY_1_DAY, WEEKLY_1_HOUR, WEEKLY_1_MINUTE, now)
        alert_time_weekly1 = next_weekly1 - timedelta(minutes=WEEKLY_1_ALERT_BEFORE)
        if is_time_match(now, alert_time_weekly1.hour, alert_time_weekly1.minute) and now.date() == alert_time_weekly1.date() and should_run_event('weekly_event_1', now, cooldown_minutes=10000):
            message = WEEKLY_1_MESSAGE.replace("{ALERT_MINUTES}", str(WEEKLY_1_ALERT_BEFORE))
            await send_message(message)
            mark_event_run('weekly_event_1', now)
        
        next_weekly2 = get_next_weekly_event_time(WEEKLY_2_DAY, WEEKLY_2_HOUR, WEEKLY_2_MINUTE, now)
        alert_time_weekly2 = next_weekly2 - timedelta(minutes=WEEKLY_2_ALERT_BEFORE)
        if is_time_match(now, alert_time_weekly2.hour, alert_time_weekly2.minute) and now.date() == alert_time_weekly2.date() and should_run_event('weekly_event_2', now, cooldown_minutes=10000):
            message = WEEKLY_2_MESSAGE.replace("{ALERT_MINUTES}", str(WEEKLY_2_ALERT_BEFORE))
            await send_message(message)
            mark_event_run('weekly_event_2', now)
    
    # === BIWEEKLY EVENTS ===
    if ENABLE_BIWEEKLY_EVENTS:
        if now.weekday() == BIWEEKLY_1_DAY:
            days_diff = (now.date() - BIWEEKLY_1_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0:
                event_time_bw1 = datetime.combine(now.date(), datetime.min.time()).replace(
                    hour=BIWEEKLY_1_HOUR, minute=BIWEEKLY_1_MINUTE, tzinfo=UTC
                )
                alert_time_bw1 = event_time_bw1 - timedelta(minutes=BIWEEKLY_1_ALERT_BEFORE)
                if is_time_match(now, alert_time_bw1.hour, alert_time_bw1.minute) and should_run_event('biweekly_event_1', now, cooldown_minutes=20000):
                    message = BIWEEKLY_1_MESSAGE.replace("{ALERT_MINUTES}", str(BIWEEKLY_1_ALERT_BEFORE))
                    await send_message(message)
                    mark_event_run('biweekly_event_1', now)
        
        if now.weekday() == BIWEEKLY_2_DAY:
            days_diff = (now.date() - BIWEEKLY_2_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0:
                event_time_bw2 = datetime.combine(now.date(), datetime.min.time()).replace(
                    hour=BIWEEKLY_2_HOUR, minute=BIWEEKLY_2_MINUTE, tzinfo=UTC
                )
                alert_time_bw2 = event_time_bw2 - timedelta(minutes=BIWEEKLY_2_ALERT_BEFORE)
                if is_time_match(now, alert_time_bw2.hour, alert_time_bw2.minute) and should_run_event('biweekly_event_2', now, cooldown_minutes=20000):
                    message = BIWEEKLY_2_MESSAGE.replace("{ALERT_MINUTES}", str(BIWEEKLY_2_ALERT_BEFORE))
                    await send_message(message)
                    mark_event_run('biweekly_event_2', now)
        
        if now.weekday() == BIWEEKLY_3_DAY:
            days_diff = (now.date() - BIWEEKLY_3_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0:
                event_time_bw3 = datetime.combine(now.date(), datetime.min.time()).replace(
                    hour=BIWEEKLY_3_HOUR, minute=BIWEEKLY_3_MINUTE, tzinfo=UTC
                )
                alert_time_bw3 = event_time_bw3 - timedelta(minutes=BIWEEKLY_3_ALERT_BEFORE)
                if is_time_match(now, alert_time_bw3.hour, alert_time_bw3.minute) and should_run_event('biweekly_event_3', now, cooldown_minutes=20000):
                    message = BIWEEKLY_3_MESSAGE.replace("{ALERT_MINUTES}", str(BIWEEKLY_3_ALERT_BEFORE))
                    await send_message(message)
                    mark_event_run('biweekly_event_3', now)
        
        if now.weekday() == BIWEEKLY_4_DAY:
            days_diff = (now.date() - BIWEEKLY_4_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 2 == 0:
                event_time_bw4 = datetime.combine(now.date(), datetime.min.time()).replace(
                    hour=BIWEEKLY_4_HOUR, minute=BIWEEKLY_4_MINUTE, tzinfo=UTC
                )
                alert_time_bw4 = event_time_bw4 - timedelta(minutes=BIWEEKLY_4_ALERT_BEFORE)
                if is_time_match(now, alert_time_bw4.hour, alert_time_bw4.minute) and should_run_event('biweekly_event_4', now, cooldown_minutes=20000):
                    message = BIWEEKLY_4_MESSAGE.replace("{ALERT_MINUTES}", str(BIWEEKLY_4_ALERT_BEFORE))
                    await send_message(message)
                    mark_event_run('biweekly_event_4', now)
    
    # === 4-WEEKLY EVENTS ===
    if ENABLE_4WEEKLY_EVENTS:
        if now.weekday() == FOURWEEKLY_1_DAY:
            days_diff = (now.date() - FOURWEEKLY_1_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 4 == 0:
                event_time_4w1 = datetime.combine(now.date(), datetime.min.time()).replace(
                    hour=FOURWEEKLY_1_HOUR, minute=FOURWEEKLY_1_MINUTE, tzinfo=UTC
                )
                alert_time_4w1 = event_time_4w1 - timedelta(minutes=FOURWEEKLY_1_ALERT_BEFORE)
                if is_time_match(now, alert_time_4w1.hour, alert_time_4w1.minute) and should_run_event('4weekly_event_1', now, cooldown_minutes=40000):
                    message = FOURWEEKLY_1_MESSAGE.replace("{ALERT_MINUTES}", str(FOURWEEKLY_1_ALERT_BEFORE))
                    await send_message(message)
                    mark_event_run('4weekly_event_1', now)
        
        if now.weekday() == FOURWEEKLY_2_DAY:
            days_diff = (now.date() - FOURWEEKLY_2_REFERENCE.date()).days
            if days_diff >= 0 and (days_diff // 7) % 4 == 0:
                event_time_4w2 = datetime.combine(now.date(), datetime.min.time()).replace(
                    hour=FOURWEEKLY_2_HOUR, minute=FOURWEEKLY_2_MINUTE, tzinfo=UTC
                )
                alert_time_4w2 = event_time_4w2 - timedelta(minutes=FOURWEEKLY_2_ALERT_BEFORE)
                if is_time_match(now, alert_time_4w2.hour, alert_time_4w2.minute) and should_run_event('4weekly_event_2', now, cooldown_minutes=40000):
                    message = FOURWEEKLY_2_MESSAGE.replace("{ALERT_MINUTES}", str(FOURWEEKLY_2_ALERT_BEFORE))
                    await send_message(message)
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
    for alert_time, name, message, alert_before in custom_alerts:
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
    for alert_time, name, message, alert_before in custom_alerts:
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
    alert_before: int = 10,
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
    message: The message to send (use {ALERT_MINUTES} as placeholder for the alert time)
    alert_before: Minutes before the event to send the alert (default: 10)
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
    
    if not (0 <= alert_before <= 1440):
        await interaction.response.send_message("❌ Alert before must be between 0 and 1440 minutes", ephemeral=True)
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
    
    # The alert will fire alert_before minutes BEFORE the event time
    alert_send_time = alert_time - timedelta(minutes=alert_before)
    
    # Check if the send time is in the past
    if alert_send_time < now:
        await interaction.response.send_message(
            f"❌ Alert would fire in the past!\nEvent time: {alert_time.strftime('%Y-%m-%d %H:%M UTC')}\nAlert send time: {alert_send_time.strftime('%Y-%m-%d %H:%M UTC')}\nCurrent time: {now.strftime('%Y-%m-%d %H:%M UTC')}",
            ephemeral=True
        )
        return
    
    # Add the alert
    custom_alerts.append((alert_time, name, message, alert_before))
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
        name="Event Time",
        value=f"<t:{int(alert_time.timestamp())}:F>",
        inline=False
    )
    embed.add_field(
        name="Alert Fires",
        value=f"<t:{int(alert_send_time.timestamp())}:F> ({alert_before} min before)",
        inline=False
    )
    embed.add_field(
        name="Time Until Alert",
        value=f"**{format_time_remaining(alert_send_time - now)}**",
        inline=False
    )
    embed.add_field(
        name="Message",
        value=message.replace("{ALERT_MINUTES}", str(alert_before)),
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
    
    for i, (alert_time, name, message, alert_before) in enumerate(custom_alerts[:10], 1):  # Show max 10
        alert_send_time = alert_time - timedelta(minutes=alert_before)
        time_remaining = alert_send_time - now
        message_preview = message[:100] + "..." if len(message) > 100 else message
        embed.add_field(
            name=f"#{i} - 🔔 {name}",
            value=f"**Event:** <t:{int(alert_time.timestamp())}:F>\n**Alert fires:** <t:{int(alert_send_time.timestamp())}:R> ({alert_before} min before)\n**In:** {format_time_remaining(time_remaining)}\n**Message:** {message_preview}",
            inline=False
        )
    
    if len(custom_alerts) > 10:
        embed.set_footer(text=f"Showing 10 of {len(custom_alerts)} alerts")
    
    await interaction.response.send_message(embed=embed)
@tree.command(name="remove", description="Remove a custom alert by its number")
async def remove_custom_alert(interaction: discord.Interaction, index: int):
    """
    Remove a custom alert using its number from /list_custom
    """
    global custom_alerts

    if not custom_alerts:
        await interaction.response.send_message("📭 No custom alerts to remove.", ephemeral=True)
        return

    if index < 1 or index > len(custom_alerts):
        await interaction.response.send_message(
            f"❌ Invalid index. Please choose a number between 1 and {len(custom_alerts)}.",
            ephemeral=True
        )
        return

    # Remove alert (index-1 because list starts at 0)
    removed_alert = custom_alerts.pop(index - 1)

    alert_time, name, message, alert_before = removed_alert

    embed = discord.Embed(
        title="🗑️ Custom Alert Removed",
        color=discord.Color.red()
    )

    embed.add_field(
        name="Removed Alert",
        value=f"🔔 {name}\n<t:{int(alert_time.timestamp())}:F>",
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

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
        print(f"    - {EVENT_48H_1_NAME}: Every 48 hours starting {EVENT_48H_1_START} (alert {EVENT_48H_1_ALERT_BEFORE} min before)")
        print(f"    - {EVENT_48H_2_NAME}: Every 48 hours starting {EVENT_48H_2_START} (alert {EVENT_48H_2_ALERT_BEFORE} min before)")
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

