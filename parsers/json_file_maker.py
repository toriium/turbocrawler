import json
import os
from datetime import datetime


class JsonFileMaker:
    def __init__(self, crawler_name: str):
        self.crawler_name = crawler_name
        self.__jsons_dir_name = "jsons_data"
        self.__jsons_dir_path = f"{os.getcwd()}/{self.__jsons_dir_name}"
        self.__file_name = None
        self.__json_file_path = None
        self.__json_today_dir = None

    def create(self, json_data: dict):
        datetime_now = datetime.now()
        date_today = datetime_now.date().strftime("%Y_%m_%d")
        time_now = datetime_now.time().strftime("%H_%M_%S_%f")

        self.__file_name = f'{time_now}.json'
        self.__json_today_dir = f"{self.__jsons_dir_path}/{self.crawler_name}/{date_today}"
        self.__json_file_path = f"{self.__json_today_dir}/{self.__file_name}"

        self.__create_file_path()

        self.__create_json_file(json_data=json_data, file_path=self.__json_file_path)

    def __create_file_path(self):
        os.makedirs(self.__json_today_dir, exist_ok=True)
        if not os.path.exists(self.__json_file_path):
            with open(self.__json_file_path, 'w'):
                ...

    @staticmethod
    def __create_json_file(json_data: dict, file_path: str):
        with open(file_path, 'w') as file:
            json.dump(json_data, file)
