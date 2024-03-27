import webuntis
from datetime import datetime
import config_manager

config = config_manager.Config("settings.json")

def get_untis_session():
    untis_username = config.get_config("untis_username")
    untis_password = config.get_config("untis_password")
    untis_server = config.get_config("untis_server")
    untis_school = config.get_config("untis_school")
    untis_useragent = config.get_config("untis_useragent")
    return webuntis.Session(username=untis_username, password=untis_password, server=untis_server, school=untis_school, useragent=untis_useragent)

def get_current_schoolyear():
    with get_untis_session().login() as session:
        start_date = session.schoolyears().current.start
        end_date = session.schoolyears().current.end
        return {'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d')}

def get_all_semesters() -> list[dict]:
    semesters = []
    with get_untis_session().login() as session:
        sorted_semesters = sorted(session.klassen(), key=lambda klasse: klasse.name)

        for semester_id, klasse in enumerate(sorted_semesters):
            semesters.append({"id": str(semester_id), "name": klasse.name})
    return semesters
    
def get_all_modules_of_semesters(semesters:list[str], start_date:datetime, end_date:datetime) -> set:
    modules = []
    _set = set()
    with get_untis_session().login() as session:
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

def get_events_from_modules(modules:list[str], semesters:list[str], start_date:datetime, end_date:datetime) -> list[dict]:
    events = []
    with get_untis_session().login() as session:
        for sem in semesters:
            klasse = session.klassen().filter(name=sem)[0]
            table = session.timetable_extended(klasse=klasse, start=start_date, end=end_date).to_table()
            for _, row in table:
                for _, periods in row:
                    if periods:
                        for period in periods:
                            for subject in period.subjects:
                                if subject.long_name in modules:
                                    events.append({
                                        'name': subject.long_name,
                                        'start': period.start,
                                        'end': period.end,
                                        'rooms': [i.name for i in period.rooms],
                                        'status': period.code
                                    })
    events = [dict(t) for t in {tuple(d.items()) for d in events}]
    return events
