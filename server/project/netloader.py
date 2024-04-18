'''
 _    _ _   _ _______ ______  _____ _______ ______ _____    ____  ______ _______       
| |  | | \ | |__   __|  ____|/ ____|__   __|  ____|  __ \  |  _ \|  ____|__   __|/\    
| |  | |  \| |  | |  | |__  | (___    | |  | |__  | |  | | | |_) | |__     | |  /  \   
| |  | | . ` |  | |  |  __|  \___ \   | |  |  __| | |  | | |  _ <|  __|    | | / /\ \  
| |__| | |\  |  | |  | |____ ____) |  | |  | |____| |__| | | |_) | |____   | |/ ____ \ 
 \____/|_| \_|  |_|  |______|_____/   |_|  |______|_____/  |____/|______|  |_/_/    \_\

'''

import os
import requests
import time
import json
import icalendar
import datetime
with open('instance/netloader.json', 'r') as f:
    foreign_ical_urls = json.load(f)
    f.close()

# instance/netloader.json contains {"Foreign Kalender Name": "https://sample.com/sample.ics"}

# ----- download icals from foreign links ----- 
for name,url in foreign_ical_urls.items():
    response = requests.get(url)
    if response.status_code == 200:
        with open("instance/foreign_icals"+name+".ics", 'wb') as f:
            f.write(response.content)
            f.close()
        with open("logs/netloader.log", 'a') as f:
            f.write((time.strftime("%d/%m/%Y-%H:%M:%S", time.localtime()) + " " + name + " downloaded successfully\n"))
            f.close()
    else:
        with open("logs/netloader.log", 'a') as f:
            f.write((time.strftime("%d/%m/%Y-%H:%M:%S", time.localtime()) + " " + name + " download failed \n"))
            f.close()

# ----- ical to json -------
directory = 'instance/foreign_icals'
foreign_calendars_raw=[]
foreign_calendars_json={}
for name in foreign_ical_urls.key():
    with open(directory + name +".ics") as f:
        cal=icalendar.Calendar.from_ical(f.read())
        events=[]
        for component in cal.walk():
            if component.name == "VEVENT":
                event = {}
                event['start'] = component.get('DTSTART').dt.strftime('%Y-%m-%d %H:%M:%S')
                event['end'] = component.get('DTEND').dt.strftime('%Y-%m-%d %H:%M:%S')
                event['name'] = component.get('SUMMARY')
                event['rooms'] = [component.get('LOCATION')]
                event['status'] = None
        events.append(event)
foreign_calendars_json[name]=events


# ----- add JSON to "untis_data.json"

# load untis_data.json here referenced as untis_data
untis_data={}
for name, data in foreign_calendars_json:
    untis_data["module_lists"]["Veranstlatungen"+name].append(name)
    untis_data["timetables"]["Veranstaltungen"+name]=foreign_calendars_json[name]
