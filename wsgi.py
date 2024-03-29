from server import app
from server import manager
from threading import Thread

if __name__ == "__main__":
    calendar_update_thread = Thread(target=manager.calendar_updater)
    calendar_update_thread.start()
    app.run(host="127.0.0.1")
