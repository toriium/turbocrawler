import logging

from turbocrawler.utils import create_file_path

formatter = logging.Formatter("%(asctime)s|%(levelname)s| %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


class LOG(logging.Logger):
    def create_plugins_handlers(self, plugins: list, crawler, run_id: str) -> list[logging.Handler]:
        handlers = []
        for plugin in plugins:
            plugin_handler = plugin.log_handler(crawler=crawler, run_id=run_id)
            if plugin_handler is not None:
                plugin_handler.setFormatter(formatter)
                self.addHandler(plugin_handler)
                handlers.append(plugin_handler)
        return handlers

    def create_console_handler(self):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)

    def create_file_handler(self, path: str) -> logging.FileHandler:
        create_file_path(path)
        file_handler = logging.FileHandler(path, mode="w")
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)
        return file_handler

    def remove_handler(self, handler: logging.Handler):
        self.removeHandler(handler)
        handler.close()


logger = LOG("turbocrawler")
logger.setLevel(logging.INFO)
logger.create_console_handler()
