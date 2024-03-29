import json
import sqlite3
import time
import traceback
import webuntis
from datetime import datetime, timedelta
from icalendar import Calendar, Event, Timezone

class Config:
    def __init__(self, config_file:str) -> None:
        self.config_file = config_file
        self.defaults = {
            "database_uri": "sqlite:///database.db",
            "database_path": "instance/database.db",
            "encryption_secret_key": "obgt5cDzktDQNZA5dg49Lg/374/o4ZGX5rOY2N/9y0RzC72Y97NdYQ2I5fGjCCO9rIh6dLZ68v1CHQMtunhW2DtvrpDqLYELogKU",
            "login_logfile": "logs/login_log.txt",
            "ical_logfile": "logs/ical_log.txt",
            "seconds_between_calendar_updates": 1800,
            "untis_username": "ITS1",
            "untis_password": "",
            "untis_server": "hepta.webuntis.com",
            "untis_school": "HS-Albstadt",
            "untis_useragent": "WebUntis Test"
        }
        self.ensure_config_exists()

    def ensure_config_exists(self):
        """Create Config File if it does not exist"""
        try:
            with open(self.config_file, 'r', encoding="utf-8") as file:
                json.load(file)
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            self.write_config_file(self.defaults)

    def read_config_file(self):
        """Read in the JSON config file"""
        try:
            with open(self.config_file, 'r', encoding="utf-8") as file:
                config = json.load(file)
            return config
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            return self.defaults

    def write_config_file(self, config) -> None:
        """Write to the JSON config file"""
        with open(self.config_file, 'w+', encoding="utf-8") as file:
            json.dump(config, file, indent=4)

    def get_config(self, key:str):
        """Read the value to the key from the config file"""
        config = self.read_config_file()
        if key in config:
            return config[key]
        elif key in self.defaults:
            self.update_config(key, self.defaults[key])
            return self.defaults[key]
        return None

    def update_config(self, key:str, value) -> None:
        """Write the key value pair the config file"""
        config = self.read_config_file()
        config[key] = value
        self.write_config_file(config)


class IcalManager:
    def __init__(self, config_file:str) -> None:
        self.config = Config(config_file=config_file)
        self.calendar_updater_status = "waiting"

    def calendar_updater(self):
        while True:
            self.calendar_updater_status = "running"
            events = self.get_all_events_from_database(user=None)
            for name in events:
                ical_data = self.create_ical(events[name])
                with open(f'calendars/{name}.calendar.ics', 'wb') as f:
                    f.write(ical_data)

            self.calendar_updater_status = "waiting"
            time.sleep(self.config.get_config("seconds_between_calendar_updates"))

    def generate_single_ical(self, user):
        event = self.get_all_events_from_database(user=user)
        ical_data = self.create_ical(event[user])
        with open(f'calendars/{user}.calendar.ics', 'wb') as file:
            file.write(ical_data)

    def create_ical(self, events:list[dict]):
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
            event_obj.add('location', list(event['rooms']))
            event_obj.add('tzid', 'Europe/Paris')
            cal.add_component(event_obj)
        return cal.to_ical()

    def get_all_events_from_database(self, user=None): # TODO WArum macht der Fehler?
        dbfile = self.config.get_config("database_path")
        events = dict()
        try:
            conn = sqlite3.connect(dbfile, check_same_thread=False)
            cursor = conn.cursor()

            data = []
            if user:
                sql = "SELECT username, semesters, modules, start_date, end_date FROM user WHERE username=?"
                data = cursor.execute(sql,(user,)).fetchall()
            else:
                sql = "SELECT username, semesters, modules, start_date, end_date FROM user"
                data = cursor.execute(sql).fetchall()
            conn.close()

            for entry in data:
                if entry:
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

                            events[username] = self.get_events_from_modules(modules=modules, semesters=semesters, start_date=start_date, end_date=end_date)
                    except json.JSONDecodeError as json_err:
                        print(f"Error parsing JSON for user {username}: {json_err}")
            return events

        except sqlite3.Error as err:
            print(err, traceback.format_exc())

# ---------- UNTIS ----------

    def get_untis_session(self):
        untis_username = self.config.get_config("untis_username")
        untis_password = self.config.get_config("untis_password")
        untis_server = self.config.get_config("untis_server")
        untis_school = self.config.get_config("untis_school")
        untis_useragent = self.config.get_config("untis_useragent")
        return webuntis.Session(username=untis_username, password=untis_password, server=untis_server, school=untis_school, useragent=untis_useragent)

    def get_current_schoolyear_from_untis(self):
        with self.get_untis_session().login() as session:
            start_date = session.schoolyears().current.start
            end_date = session.schoolyears().current.end
            return {'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d')}

    def get_all_semesters_from_untis(self) -> list[dict]:
        semesters = []
        with self.get_untis_session().login() as session:
            sorted_semesters = sorted(session.klassen(), key=lambda klasse: klasse.name)

            for semester_id, klasse in enumerate(sorted_semesters):
                semesters.append({"id": str(semester_id), "name": klasse.name})
        return semesters

    def get_all_modules_of_semesters_from_untis(self, semesters:list[str], start_date:datetime, end_date:datetime) -> set:
        modules = []
        _set = set()
        with self.get_untis_session().login() as session:
            for sem in semesters:
                klasse = session.klassen().filter(name=sem)[0]
                table = session.timetable_extended(klasse=klasse, start=start_date, end=end_date).to_table()
                for _, row in table:
                    for _, periods in row:
                        if periods:
                            for period in periods:
                                for subject in period.subjects:
                                    _set.add(subject.long_name)
        for module_id, module_name in enumerate(sorted(list(_set))):
                modules.append({"id": str(module_id), "name": module_name})
        return modules

    def get_events_from_modules(self, modules:list[str], semesters:list[str], start_date:datetime, end_date:datetime) -> list[dict]:
        events = []
        processed = set()
        with self.get_untis_session().login() as session:
            for sem in semesters:
                klasse = session.klassen().filter(name=sem)
                if not klasse:
                    print(f"No class found for semester {sem}")
                    continue
                klasse = klasse[0]
                table = session.timetable_extended(klasse=klasse, start=start_date, end=end_date).to_table()
                for _, row in table:
                    for _, periods in row:
                        if periods:
                            for period in periods:
                                for subject in period.subjects:
                                    if subject.long_name in modules:
                                        rooms = []
                                        try:
                                            rooms = [i.name for i in period.rooms]
                                        except IndexError: # For some unknown reason, period.rooms is not found sometimes (correlates with "ro": {"id": 0}) --> Dirty fix: catch it and dont care about the room
                                            rooms = ["None"]
                                        events.append({
                                            'name': subject.long_name,
                                            'start': period.start if hasattr(period, 'start') else None,
                                            'end': period.end if hasattr(period, 'end') else None,
                                            'rooms': tuple(rooms),
                                            'status': period.code if hasattr(period, 'code') else None
                                        })
                                        processed.add(subject.long_name)
        events = [dict(t) for t in {tuple(d.items()) for d in events}]
        return events

# ---------- LOG ----------

    def log_ical_request(self, ip_address, user):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.config.get_config("ical_logfile"), "a") as log_file:
            log_file.write(f"{timestamp}: '{ip_address}' requested calendar for '{user}'\n")

    def log_login(self, user):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.config.get_config("login_logfile"), "a") as log_file:
            log_file.write(f"{timestamp}: '{user}' logged in\n")