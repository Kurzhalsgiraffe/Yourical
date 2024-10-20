import json
import sqlite3
import traceback
import webuntis
import requests
import time
import icalendar
from datetime import datetime, timedelta
from icalendar import Calendar, Event, Timezone
import pytz

def sql_error_handler(err,trace):
    """Print Errors that can occurr in the DB Methods"""
    print(f"SQLite error: {err.args}")
    print("Exception class is: ", err.__class__)
    print("SQLite traceback: ")
    print(trace)

class Config:
    def __init__(self, config_file:str) -> None:
        self.config_file = config_file
        self.defaults = {
            "additional_calendars": {},
            "banned_usernames": ["admin", "root", "username", "user", "sia", "vdi"],
            "database_uri": "sqlite:///database.db",
            "database_path": "instance/database.db",
            "encryption_secret_key": "secret",
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

class Dao:
    def __init__(self, dbfile:str) -> None:
        try:
            sqlite3.threadsafety = 1
            self.dbfile = dbfile
        except sqlite3.Error as err:
            sql_error_handler(err,traceback.format_exc())

    def get_db_connection(self) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
        """Get a connection to the database"""
        try:
            conn = sqlite3.connect(self.dbfile, check_same_thread=False)
            cursor = conn.cursor()
            return conn, cursor
        except sqlite3.Error as err:
            sql_error_handler(err,traceback.format_exc())

    def get_all_events_from_database(self, user=None) -> list:
        try:
            data = []
            conn, cursor = self.get_db_connection()
            if user:
                sql = "SELECT username, semesters, modules, additional_calendars FROM user WHERE username=?"
                data = cursor.execute(sql,(user,)).fetchall()
            else:
                sql = "SELECT username, semesters, modules, additional_calendars FROM user"
                data = cursor.execute(sql).fetchall()
            conn.close()
            return data
        except sqlite3.Error as err:
            sql_error_handler(err,traceback.format_exc())
            return None

    def set_last_calendar_update(self, user) -> None:
        try:
            conn, cursor = self.get_db_connection()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = "UPDATE user SET last_calendar_update=? WHERE username=?"
            cursor.execute(sql,(now, user))
            conn.commit()
            conn.close()
        except sqlite3.Error as err:
            sql_error_handler(err,traceback.format_exc())

    def get_last_calendar_update(self, user) -> None:
        try:
            conn, cursor = self.get_db_connection()
            sql = "SELECT last_calendar_update FROM user WHERE username=?"
            last_calendar_update = cursor.execute(sql,(user,)).fetchone()
            conn.close()
            if last_calendar_update:
                return last_calendar_update[0]
            else:
                return None
        except sqlite3.Error as err:
            sql_error_handler(err,traceback.format_exc())
            return None
        
    def get_user_count(self):
        try:
            conn, cursor = self.get_db_connection()
            sql = "SELECT COUNT(username) FROM user WHERE 1=1"
            result = cursor.execute(sql).fetchone()
            conn.close()
            if result:
                return result[0]
            else:
                return "Fetch unsuccessfull"
        except sqlite3.Error as err:
            sql_error_handler(err,traceback.format_exc())
            return None


    def get_active_user_count(self):
        try:
            conn, cursor = self.get_db_connection()
            today = datetime.now()
            five_days_ago = today - timedelta(days=5)
            five_days_ago_str = five_days_ago.strftime('%Y-%m-%d %H:%M:%S')

            sql = "SELECT COUNT(username) FROM user WHERE last_calendar_pull IS NOT NULL AND last_calendar_pull >= ?"

            result = cursor.execute(sql, (five_days_ago_str,)).fetchone()
            conn.close()

            if result:
                return result[0]
            else:
                return "Fetch unsuccessful"
        except sqlite3.Error as err:
            sql_error_handler(err, traceback.format_exc())
            return None


class UntisHandler:
    def __init__(self, save_file:str, config:Config) -> None:
        self.save_file = save_file
        self.config = config
        self.data = {}
        self.ensure_untis_data_exists()

    def ensure_untis_data_exists(self):
        try:
            with open(self.save_file, "r", encoding="utf-8") as file:
                self.data = json.load(file)
                if "schoolyear" not in self.data or "module_lists" not in self.data or "timetables" not in self.data:
                    raise ValueError()
        except (json.JSONDecodeError, FileNotFoundError, OSError, ValueError) as e:
            self.update_schoolyear_from_untis()
            self.update_all_tables_from_untis()

    def save_as_json(self):
        with open(self.save_file, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4, ensure_ascii=False)

    # ---------- UNTIS API ----------

    def get_untis_session(self):
        untis_username = self.config.get_config("untis_username")
        untis_password = self.config.get_config("untis_password")
        untis_server = self.config.get_config("untis_server")
        untis_school = self.config.get_config("untis_school")
        untis_useragent = self.config.get_config("untis_useragent")
        return webuntis.Session(username=untis_username, password=untis_password, server=untis_server, school=untis_school, useragent=untis_useragent)

    def update_schoolyear_from_untis(self):
        with self.get_untis_session().login() as session:
            schoolyear = session.schoolyears().current
            self.data["schoolyear"] = {"start_date": schoolyear.start.strftime("%Y-%m-%d"), "end_date": schoolyear.end.strftime("%Y-%m-%d")}
        self.save_as_json()

    def update_all_tables_from_untis(self):
        schoolyear = self.get_current_schoolyear()
        start_date = datetime.strptime(schoolyear["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(schoolyear["end_date"], "%Y-%m-%d")

        semesters = []
        self.data["module_lists"] = dict()
        self.data["timetables"] = dict()

        with self.get_untis_session().login() as session:
            for klasse in session.klassen():
                if klasse:
                    semesters.append(klasse.name)
                    module_list = set()
                    timetable = []
                    table = session.timetable_extended(klasse=klasse, start=start_date, end=end_date).to_table()
                    for _, row in table:
                        for _, periods in row:
                            if periods:
                                for period in periods:
                                    for subject in period.subjects:
                                        module_list.add(subject.long_name)
                                        rooms = []
                                        try:
                                            rooms = [i.name for i in period.rooms]
                                        except IndexError: # For some unknown reason, period.rooms is not found sometimes (correlates with "ro": {"id": 0}) --> Dirty fix: catch it and dont care about the room
                                            rooms = ["None"]
                                        timetable.append({
                                            'name': subject.long_name,
                                            'start': period.start.strftime('%Y-%m-%d %H:%M:%S') if hasattr(period, 'start') else None,
                                            'end': period.end.strftime('%Y-%m-%d %H:%M:%S') if hasattr(period, 'end') else None,
                                            'rooms': rooms,
                                            'status': period.code if hasattr(period, 'code') else None
                                        })
                    self.data["module_lists"][klasse.name] = list(module_list)
                    self.data["timetables"][klasse.name] = timetable
                self.data["semesters"] = sorted(semesters)
        self.save_as_json()

# ---------- ACCESS METHODS ----------

    def get_current_schoolyear(self):
        schoolyear = self.data.get("schoolyear")
        return schoolyear

    def get_module_list_of_semesters(self, semesters:str):
        _set = set()
        modules = []
        module_lists = self.data.get("module_lists")
        if module_lists:
            for sem in semesters:
                m = module_lists.get(sem)
                if m:
                    _set.update(m)
        for module_id, module_name in enumerate(sorted(list(_set))):
            modules.append({"id": str(module_id), "name": module_name})
        return modules

    def get_events_from_modules(self, semesters:list[str], modules:list[str]):
        events = []
        timetables = self.data.get("timetables")
        for sem in semesters:
            if sem in timetables:
                for event in timetables[sem]:
                    if event:
                        if event.get("name") in modules:
                            event["rooms"] = tuple(event["rooms"])
                            events.append(event)
        events = [dict(t) for t in {tuple(d.items()) for d in events}]
        return events

class Netloader:
    def __init__(self, save_file:str, config:Config) -> None:
        self.save_file = save_file
        self.config = config
        self.data = {}
        self.ensure_netloader_data_exists()

    def ensure_netloader_data_exists(self):
        try:
            with open(self.save_file, "r", encoding="utf-8") as file:
                self.data = json.load(file)
                if "timetables" not in self.data or "names" not in self.data:
                    raise ValueError()
        except (json.JSONDecodeError, FileNotFoundError, OSError, ValueError) as e:
            self.download_additional_calendars()
            self.icals_to_event_list()

    def save_as_json(self):
        with open(self.save_file, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4, ensure_ascii=False)

    def log(self, message:str):
        try:
            with open("logs/netloader.log", 'a') as f: # TODO: logfile to config
                f.write((time.strftime("%d/%m/%Y-%H:%M:%S", time.localtime()) + " " + message + "\n"))
        except FileNotFoundError:
            print("Couldn't write logmessage into netloader.log")

    def download_additional_calendars(self):
        additional_calendars = self.config.get_config("additional_calendars")

        for name, url in additional_calendars.items():
            response = requests.get(url)
            if response.status_code == 200:
                try:
                    with open("calendars/"+name+".calendar.ics", 'wb') as file: # TODO: config
                        file.write(response.content)
                except FileNotFoundError:
                    self.log(name+" --- some issue saving the file after download")
                self.log(name + " downloaded successfully")
            else:
                self.log(name + "HTTP != 200")

    def icals_to_event_list(self):
        self.data["timetables"] = {}
        self.data["names"] = []
        netloader_json={}
        additional_calendars = self.config.get_config("additional_calendars")
        for name, url in additional_calendars.items():
            try:
                with open('calendars/' + name +".calendar.ics") as f:
                    cal=icalendar.Calendar.from_ical(f.read())
            except FileNotFoundError:
                self.log(name +"couldn't open " + name + "calendar.ics")

            eventlist=[]
            for component in cal.walk():
                if component.name == "VEVENT":
                    timezone_de = pytz.timezone('Europe/Paris')
                    date_format = "%Y-%m-%d %H:%M:%S"
                    event = {}
                    start_utc = component.get('DTSTART').dt.strftime('%Y-%m-%d %H:%M:%S')
                    end_utc = component.get('DTEND').dt.strftime('%Y-%m-%d %H:%M:%S')
                    start_naive = datetime.strptime(start_utc, date_format)
                    end_naive = datetime.strptime(end_utc, date_format)
                    start_aware = pytz.utc.localize(start_naive)
                    end_aware = pytz.utc.localize(end_naive)
                    start_local = start_aware.astimezone(timezone_de)
                    end_local = end_aware.astimezone(timezone_de)
                    event['start'] = start_local.strftime('%Y-%m-%d %H:%M:%S')
                    event['end'] = end_local.strftime('%Y-%m-%d %H:%M:%S')
                    event['name'] = component.get('SUMMARY')
                    event['rooms'] = [component.get('LOCATION')]
                    event['status'] = None
                    eventlist.append(event)
            netloader_json[name]=eventlist

        for name, events in netloader_json.items():
            self.data["timetables"][name]=events
            self.data["names"].append(name)
        self.save_as_json()

    def get_events_from_calendars(self, additional_calendars):
        events = []
        timetables = self.data.get("timetables")
        for cal in additional_calendars:
            if cal in timetables:
                for event in timetables[cal]:
                    if event:
                        events.append(event)
        return events

class IcalManager:
    def __init__(self, config_file:str) -> None:
        self.config = Config(config_file=config_file)
        self.database = Dao(dbfile=self.config.get_config("database_path"))
        self.untis_handler = UntisHandler(save_file="instance/untis_data.json", config=self.config) #TODO: zur Config
        self.netloader = Netloader(save_file="instance/netloader.json", config=self.config)
        self.generate_all_icals()

    def generate_all_icals(self):
        events = self.get_all_events(user=None)
        for user in events:
            self.create_ical(user, events[user])

    def generate_single_ical(self, user):
        events = self.get_all_events(user=user)
        self.create_ical(user, events[user])

    def create_ical(self, user, events:list[dict]):
        cal = Calendar()
        timezone = Timezone()
        timezone.add('TZID', 'Europe/Paris')
        cal.add('X-WR-TIMEZONE', 'Europe/Paris')
        cal.add_component(timezone)

        for event in events:
            event_obj = Event()
            if event['status'] == "cancelled":
                event_obj.add('summary', f"ENTFÄLLT: {event['name']}")
            else:
                event_obj.add('summary', event['name'])
            event_obj.add('dtstart', datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S'))
            event_obj.add('dtend', datetime.strptime(event['end'], '%Y-%m-%d %H:%M:%S'))
            event_obj.add('location', list(event['rooms']))
            cal.add_component(event_obj)

        ical_data =  cal.to_ical()
        with open(f'calendars/{user}.calendar.ics', 'wb') as f:
            f.write(ical_data)

        self.database.set_last_calendar_update(user)

    def get_all_events(self, user=None):
        events = dict()
        data = self.database.get_all_events_from_database(user)

        for entry in data:
            if entry:
                try:
                    username = entry[0]
                    semesters_json = entry[1]
                    modules_json = entry[2]
                    additional_calendars_json = entry[3]

                    events[username] = []

                    if semesters_json and modules_json:
                        modules = json.loads(modules_json)
                        semesters = json.loads(semesters_json)
                        events[username].extend(self.untis_handler.get_events_from_modules(semesters=semesters, modules=modules))

                    if additional_calendars_json:
                        additional_calendars = json.loads(additional_calendars_json)
                        events[username].extend(self.netloader.get_events_from_calendars(additional_calendars=additional_calendars))

                except json.JSONDecodeError as json_err:
                    print(f"Error parsing JSON for user {username}: {json_err}")
        return events

    def get_semester_list(self, selected_semesters, selected_additionals):
        lst = []
        semester_list = []
        semesters = self.untis_handler.data.get("semesters")
        additional_calendars = self.netloader.data.get("names")

        if semesters is not None:
            lst.extend(semesters)
        if additional_calendars is not None:
            lst.extend(additional_calendars)

        if lst:
            for id, name in enumerate(lst):
                semester_list.append({"id": str(id), "name": name})
            for i in semester_list:
                i["selected"] = (selected_semesters is not None and i["name"] in selected_semesters) or (selected_additionals is not None and i["name"] in selected_additionals)

        return semester_list

# ---------- LOGGING ----------

    def log_ical_request(self, ip_address, user):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.config.get_config("ical_logfile"), "a") as log_file:
            log_file.write(f"{timestamp}: '{ip_address}' requested calendar for '{user}'\n")

    def log_login(self, user):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.config.get_config("login_logfile"), "a") as log_file:
            log_file.write(f"{timestamp}: '{user}' logged in\n")
