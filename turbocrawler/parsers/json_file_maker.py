import json
from datetime import datetime
from pathlib import Path


class JsonFileMaker:
    def __init__(self, crawler_name: str):
        self.crawler_name = crawler_name
        self.__jsons_dir_name = "jsons_data"
        self.__jsons_dir_path = Path.cwd() / self.__jsons_dir_name
        self.__file_name = None
        self.__json_file_path = None
        self.__json_today_dir = None

    def create(self, json_data: dict):
        datetime_now = datetime.now()
        date_today = datetime_now.date().strftime("%Y_%m_%d")
        time_now = datetime_now.time().strftime("%H_%M_%S_%f")

        self.__file_name = f"{time_now}.json"
        self.__json_today_dir = self.__jsons_dir_path / self.crawler_name / date_today
        self.__json_file_path = self.__json_today_dir / self.__file_name

        self.__create_file_path()

        self.__create_json_file(json_data=json_data, file_path=self.__json_file_path)

    def __create_file_path(self):
        self.__json_today_dir.mkdir(parents=True, exist_ok=True)
        self.__json_file_path.touch(exist_ok=True)

    @staticmethod
    def __create_json_file(json_data: dict, file_path: Path):
        with open(file_path, "w") as file:
            json.dump(json_data, file)
