import webuntis
from datetime import datetime

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
                                            'rooms': [i.name for i in period.rooms],
                                            'rooms_long': [i.long_name for i in period.rooms]
                                        })
    return events
