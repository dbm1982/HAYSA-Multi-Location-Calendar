from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from html import unescape
import pytz
import re
import os
import time

# CONFIGURATION
START_DATE = datetime(2025, 10, 17)
END_DATE = datetime(2025, 10, 19)
URL = "https://haysa.org/multi-location-calendar"
DELAY = 2  # seconds between page loads
TIMEZONE = pytz.timezone("America/New_York")
ICS_FILENAME = "haysa_schedule.ics"

# SETUP
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

def clean(text):
    return unescape(re.sub(r"<[^>]+>", "", text)).strip()

def extract_events(date_str):
    events = []
    raw = driver.page_source
    blocks = raw.split("Practice:")
    for block in blocks[1:]:
        try:
            team = clean(block.split("Practice")[0])
            field_line = next((line for line in block.splitlines() if "Field" in line and "," in line and "(" in line), "")
            field = clean(field_line.split(",")[0])
            location = clean(field_line.split(",")[1].split("(")[0])
            time_range = clean(field_line.split("(")[1].split(")")[0])
            start_str, end_str = time_range.split("-")
            start = TIMEZONE.localize(datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %I:%M%p"))
            end = TIMEZONE.localize(datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %I:%M%p"))

            events.append({
                "summary": f"Practice: {team}",
                "start": start,
                "end": end,
                "location": f"{field}, {location}",
                "uid": f"{date_str}-{team.replace(' ', '')}@haysa.org"
            })
        except Exception as e:
            print(f"⚠️ Skipped block due to error: {e}")
    return events

# MAIN LOOP
print("🚀 Starting scrape...")
all_events = []
current_date = START_DATE

while current_date <= END_DATE:
    date_str = current_date.strftime("%Y-%m-%d")
    print(f"📅 Scraping {date_str}")
    driver.get(f"{URL}?date={date_str}")
    time.sleep(DELAY)
    all_events.extend(extract_events(date_str))
    current_date += timedelta(days=1)

driver.quit()

# GENERATE ICS
cal = Calendar()
cal.add("prodid", "-//HAYSA Practice Calendar//haysa.org//")
cal.add("version", "2.0")

for e in all_events:
    event = Event()
    event.add("summary", e["summary"])
    event.add("dtstart", e["start"])
    event.add("dtend", e["end"])
    event.add("location", e["location"])
    event.add("description", "Imported from HAYSA calendar")
    event["uid"] = e["uid"]
    cal.add_component(event)

with open(ICS_FILENAME, "wb") as f:
    f.write(cal.to_ical())

print(f"✅ Done! ICS file saved to: {ICS_FILENAME}")
