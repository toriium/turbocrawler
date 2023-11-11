from turbocrawler import CrawlerRunner, Crawler
from turbocrawler.engine.data_types.crawler_runner_config import CrawlerRunnerConfig
import argparse


class CrawlersOrchestrator:
    def __init__(self):
        self.targets: list[tuple[type[Crawler], CrawlerRunnerConfig]] = []

    def add(self, crawler: type[Crawler], config: CrawlerRunnerConfig):
        self.targets.append((crawler, config))

    def start(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c',
                            '--crawler',
                            help='The target crawler name. Example --crawler crawlerLaptop')
        args = parser.parse_args()
        crawler_name = args.crawler

        for target in self.targets:
            if target[0].crawler_name == crawler_name:
                target_crawler = target
                break
        else:
            raise ValueError(f"Crawler with {crawler_name} crawler_name not found")

        crawler = target_crawler[0]
        config = target_crawler[1]

        CrawlerRunner(crawler=crawler, config=config).run()
