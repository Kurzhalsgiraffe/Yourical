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

def get_events_from_database():
    dbfile = config.get_config("database_path")
    events = dict()
    try:
        conn = sqlite3.connect(dbfile, check_same_thread=False)
        cursor = conn.cursor()

        sql = "SELECT username, semesters, modules FROM user"
        data = cursor.execute(sql).fetchall()
        
        for entry in data:       
            try:
                username = entry[0]
                semesters_json = entry[1]
                modules_json = entry[2]
                modules = json.loads(modules_json)
                semesters = json.loads(semesters_json)

                events[username] = untis.get_events_from_modules(modules=modules, semesters=semesters, start_date=start_date, end_date=end_date)
            except json.JSONDecodeError as json_err:
                print(f"Error parsing JSON for user {username}: {json_err}")

        conn.close()
        return events

    except sqlite3.Error as err:
        print(err, traceback.format_exc())



if __name__ == "__main__":
    start_date = datetime.strptime(config.get_config("start_date"), '%Y-%m-%d')
    end_date = datetime.strptime(config.get_config("end_date"), '%Y-%m-%d')

    events = get_events_from_database()
    for name in events:
        ical_data = create_ical(events[name])
        with open(f'calendars/{name}.calendar.ics', 'wb') as f:
            f.write(ical_data)