import json

class Config:
    def __init__(self, config_file:str) -> None:
        self.config_file = config_file
        self.defaults = {
            "database_uri": "sqlite:///database.db",
            "database_path": "instance/database.db",
            "encryption_secret_key": "thisisasecretkey",
            "start_date": "2024-03-18",
            "end_date": "2024-07-06",
            "minimum_start_date": "2024-03-18",
            "maximum_end_date": "2024-07-06",
            "untis_username": "ITS1",
            "untis_password": "",
            "untis_server": "hepta.webuntis.com",
            "untis_school": "HS-Albstadt",
            "untis_useragent": "WebUntis Test"
        }

    def read_config_file(self):
        """Read in the JSON config file"""
        with open(self.config_file, 'r', encoding="utf-8") as file:
            config = json.load(file)
        return config

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
            value = self.defaults[key]
            self.update_config(key, value)
            return value
        return None

    def update_config(self, key:str, value) -> None:
        """Write the key value pair the config file"""
        config = self.read_config_file()
        config[key] = value
        self.write_config_file(config)