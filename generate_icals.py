import config_manager
import json
import sqlite3
import traceback
import untis
from datetime import datetime, timedelta
from icalendar import Calendar, Event, Timezone

config = config_manager.Config("settings.json")

def create_ical(events:list[dict]):
    timezone = Timezone()
    timezone.add('TZID', 'Europe/Paris')

    standard_time = Timezone()
    standard_time.add('DTSTART', datetime(1970, 1, 1, 0, 0, 0))
    standard_time.add('TZOFFSETTO', timedelta(hours=1))  # Offset von UTC
    standard_time.add('TZOFFSETFROM', timedelta(hours=0))  # Offset zu UTC

    daylight_time = Timezone()
    daylight_time.add('DTSTART', datetime(1970, 1, 1, 0, 0, 0))
    daylight_time.add('TZOFFSETTO', timedelta(hours=2))  # Offset von UTC
    daylight_time.add('TZOFFSETFROM', timedelta(hours=1))  # Offset zu UTC
    daylight_time.add('RRULE', {'FREQ': 'YEARLY', 'BYMONTH': 3, 'BYDAY': '-1SU', 'TZOFFSETFROM': timedelta(hours=1), 'TZOFFSETTO': timedelta(hours=2)})  # Sommerzeitregel

    timezone.add_component(standard_time)
    timezone.add_component(daylight_time)
    cal = Calendar()
    cal.add('X-WR-TIMEZONE', 'Europe/Paris')
    cal.add_component(timezone)

    for event in events:
        event_obj = Event()
        if event['status'] == "cancelled":
            event_obj.add('summary', f"ENTFÄLLT: {event['name']}")
        else:
            event_obj.add('summary', event['name'])
        event_obj.add('dtstart', event['start'])
        event_obj.add('dtend', event['end'])
        event_obj.add('location', event['rooms'])
        event_obj.add('tzid', 'Europe/Paris')
        cal.add_component(event_obj)

    return cal.to_ical()

def get_all_events_from_database(user=None):
    dbfile = config.get_config("database_path")
    events = dict()
    try:
        conn = sqlite3.connect(dbfile, check_same_thread=False)
        cursor = conn.cursor()

        if user:
            sql = "SELECT username, semesters, modules, start_date, end_date FROM user WHERE username=?"
            data = cursor.execute(sql,(user,)).fetchall()
        else:
            sql = "SELECT username, semesters, modules, start_date, end_date FROM user"
            data = cursor.execute(sql).fetchall()

        for entry in data:
            try:
                username = entry[0]
                semesters_json = entry[1]
                modules_json = entry[2]
                start_date_str = entry[3]
                end_date_str = entry[4]

                if semesters_json and modules_json:
                    modules = json.loads(modules_json)
                    semesters = json.loads(semesters_json)
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

                    events[username] = untis.get_events_from_modules(modules=modules, semesters=semesters, start_date=start_date, end_date=end_date)
            except json.JSONDecodeError as json_err:
                print(f"Error parsing JSON for user {username}: {json_err}")

        conn.close()
        return events

    except sqlite3.Error as err:
        print(err, traceback.format_exc())

def generate_icals(user=None):
    events = get_all_events_from_database(user=user)
    for name in events:
        ical_data = create_ical(events[name])
        with open(f'calendars/{name}.calendar.ics', 'wb') as f:
            f.write(ical_data)


if __name__ == "__main__":
    generate_icals()