from server import app
from server import update_calendars

update_calendars() # This will start the update when the Server is started. Disable it while API is bugged, because when this fails the server wont even start