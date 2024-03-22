from datetime import datetime
import json
import sqlite3
import traceback
import config_manager
import untis
from icalendar import Calendar, Event

config = config_manager.Config("settings.json")

def create_ical(events:list[dict]):
    cal = Calendar()
    for event in events:
        event_obj = Event()
        event_obj.add('summary', event['name'])
        event_obj.add('dtstart', event['start'])
        event_obj.add('dtend', event['end'])
        event_obj.add('location', event['rooms'])
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