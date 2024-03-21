import webuntis
from datetime import datetime
from icalendar import Calendar, Event

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

def get_untis_session():
    untis_username = "ITS1"
    untis_password = ""
    untis_server = "hepta.webuntis.com"
    untis_school = "HS-Albstadt"
    untis_useragent = "WebUntis Test"
    return webuntis.Session(username=untis_username, password=untis_password, server=untis_server, school=untis_school, useragent=untis_useragent)

def get_all_semesters() -> list[dict]:
    semesters = []
    with get_untis_session().login() as session:
        sorted_semesters = sorted(session.klassen(), key=lambda klasse: klasse.name)

        for semester_id, klasse in enumerate(sorted_semesters):
            semesters.append({"id": str(semester_id), "name": klasse.name})
    return semesters
    
def get_all_modules_of_semesters(semesters:list[str], start:datetime, end:datetime) -> set:
    modules = []
    _set = set()
    with get_untis_session().login() as session:
        for sem in semesters:
            klasse = session.klassen().filter(name=sem)[0]
            table = session.timetable_extended(klasse=klasse, start=start, end=end).to_table()
            for _, row in table:
                for _, periods in row:
                    if periods:
                        for period in periods:
                            for subject in period.subjects:
                                _set.add(subject.long_name)
    for module_id, module_name in enumerate(sorted(list(_set))):
            modules.append({"id": str(module_id), "name": module_name})
    return modules

def get_events_from_modules(modules:list[str], semesters:list[str], start:datetime, end:datetime) -> list[dict]:
    events = []
    with get_untis_session().login() as session:
        for sem in semesters:
            klasse = session.klassen().filter(name=sem)[0]
            table = session.timetable_extended(klasse=klasse, start=start, end=end).to_table()
            for _, row in table:
                for _, periods in row:
                    if periods:
                        for period in periods:
                            if period.code != "cancelled":
                                for subject in period.subjects:
                                    if subject.long_name in modules:
                                        events.append({
                                            'name': subject.long_name,
                                            'start': period.start,
                                            'end': period.end,
                                            'rooms': period.rooms
                                        })
    return events



if __name__ == "__main__":
    # all_semesters = get_all_semesters()
    # all_modules = get_all_modules_of_semesters(all_semesters[:3], start=start_date, end=end_date)
    # print(all_modules)

    start_date = datetime(2024, 3, 18)
    end_date = datetime(2024, 7, 6)

    modules = ["Praktikum Maschinelles Lernen",
            "Maschinelles Lernen",
            "Security und Internet der Dinge",
            "Projekt Security und Internet der Dinge",
            "Sensoren und Aktoren",
            "Chipdesign",
            "WPM_Innovation and Transfer Competence",
            "WPM Advanced Programming"
            ]

    semesters = ["SE-AC_SS"]

    events = get_events_from_modules(modules=modules, semesters=semesters, start=start_date, end=end_date)
    ical_data = create_ical(events)

    with open('my_calendar.ics', 'wb') as f:
        f.write(ical_data)