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


class Config:
    def __init__(self, config_file:str) -> None:
        self.config_file = config_file
        self.defaults = {
            "banned_usernames": ["admin", "root", "sia", "vdi"],
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

    def netload(self):
        def netloader_log(message:str):
            try:
                with open("logs/netloader.log", 'a') as f:
                    f.write((time.strftime("%d/%m/%Y-%H:%M:%S", time.localtime()) + " " + message + "\n"))
                    f.close()
            except FileNotFoundError:
                print("Couldnt write logmessage into netloader.log")
        try:
            with open("instance/netloader.json", 'r') as f:
                netloader_urls = json.load(f)
                f.close()
        except FileNotFoundError:
            netloader_log("configure instance/netloader.json to load url calendars into your application \{'sample':'sample.com/file.ics'\}")
            

        # ----- download icals from foreign links ----- 
        for name,url in netloader_urls.items():
            response = requests.get(url)
            if response.status_code == 200:
                try:
                    with open("calendars/"+name+".calendar.ics", 'wb') as f:
                        f.write(response.content)
                        f.close()
                except FileNotFoundError:
                    netloader_log(name+" --- some issue saving the file after download")
                netloader_log(name + " downloaded successfully")
            else:
                netloader_log(name + "HTTP != 200")

        # ----- ical to json -------
        netloader_json={}
        for name,url in netloader_urls.items():
            try:
                with open('calendars/' + name +".calendar.ics") as f:
                    cal=icalendar.Calendar.from_ical(f.read())
                    eventlist=[]
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            utc_timezone = pytz.utc
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
            except FileNotFoundError:
                netloader_log(name +"couldn't open " + name + "calendar.ics")
        for name, events in netloader_json.items():
            self.data["module_lists"][name]=[]
            self.data["module_lists"][name].append(name)
            self.data["timetables"][name]=events
            self.data["semesters"].append(name)


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
        self.netload()
        self.save_as_json()

# ---------- ACCESS METHODS ----------

    def get_current_schoolyear(self):
        schoolyear = self.data.get("schoolyear")
        return schoolyear

    def get_all_semesters(self):
        semester_list = []
        semesters = self.data.get("semesters")
        for semester_id, semester_name in enumerate(semesters):
            semester_list.append({"id": str(semester_id), "name": semester_name})
        return semester_list

    def get_module_list_of_semesters(self, semesters:str):
        _set = set()
        modules = []
        module_lists = self.data.get("module_lists")
        for sem in semesters:
            _set.update(module_lists.get(sem))
        for module_id, module_name in enumerate(sorted(list(_set))):
            modules.append({"id": str(module_id), "name": module_name})
        return modules

    def get_events_from_modules(self, semesters:list[str], modules:list[str]):
        events = []
        timetables = self.data.get("timetables")
        for sem in semesters:
            try:  #----this part is only needed if u use netloader---
                with open("instance/netloader.json", 'r') as f:
                    netloader_urls = json.load(f)
                    f.close()
            except FileNotFoundError:
                self.netload().netloader_log("configure instance/netloader.json to load url calendars into your application \{'sample':'sample.com/file.ics'\}")
            if sem in netloader_urls.keys():
                for event in timetables.get(sem):
                    event["rooms"] = tuple(event["rooms"])
                    events.append(event)
            else: # --- netloader code ends here
                for event in timetables.get(sem):
                    if event:
                        if event.get("name") in modules:
                            event["rooms"] = tuple(event["rooms"])
                            events.append(event)
        events = [dict(t) for t in {tuple(d.items()) for d in events}]
        return events

class IcalManager:
    def __init__(self, config_file:str, untis_file:str) -> None:
        self.config = Config(config_file=config_file)
        self.untis_handler = UntisHandler(save_file=untis_file, config=self.config)
        self.generate_all_icals()

    def generate_all_icals(self):
        events = self.get_all_events_from_database(user=None)
        for user in events:
            self.create_ical(user, events[user])

    def generate_single_ical(self, user):
        event = self.get_all_events_from_database(user=user)
        self.create_ical(user, event[user])

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
        self.log_ical_update(user)

    def get_all_events_from_database(self, user=None):
        dbfile = self.config.get_config("database_path")
        events = dict()
        try:
            conn = sqlite3.connect(dbfile, check_same_thread=False)
            cursor = conn.cursor()

            data = []
            if user:
                sql = "SELECT username, semesters, modules FROM user WHERE username=?"
                data = cursor.execute(sql,(user,)).fetchall()
            else:
                sql = "SELECT username, semesters, modules FROM user"
                data = cursor.execute(sql).fetchall()
            conn.close()

            for entry in data:
                if entry:
                    try:
                        username = entry[0]
                        semesters_json = entry[1]
                        modules_json = entry[2]

                        if semesters_json and modules_json:
                            modules = json.loads(modules_json)
                            semesters = json.loads(semesters_json)

                            events[username] = self.untis_handler.get_events_from_modules(semesters=semesters, modules=modules)
                    except json.JSONDecodeError as json_err:
                        print(f"Error parsing JSON for user {username}: {json_err}")
            return events

        except sqlite3.Error as err:
            print(err, traceback.format_exc())

# ---------- LOG ----------

    def log_ical_request(self, ip_address, user):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.config.get_config("ical_logfile"), "a") as log_file:
            log_file.write(f"{timestamp}: '{ip_address}' requested calendar for '{user}'\n")

    def log_ical_update(self, user):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.config.get_config("ical_logfile"), "a") as log_file:
            log_file.write(f"{timestamp}: updated/created calendar for '{user}'\n")

    def log_login(self, user):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.config.get_config("login_logfile"), "a") as log_file:
            log_file.write(f"{timestamp}: '{user}' logged in\n")



manager = IcalManager("config/settings.json", untis_file="instance/untis_data.json")
