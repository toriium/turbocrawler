import argparse
import asyncio
import importlib.util
import sys
from pathlib import Path

from turbocrawler.engine.crawler import Crawler
from turbocrawler.engine.runners.crawler_runner import CrawlerRunner

CRAWLERS_FILE = "crawlers.py"


def _load_crawlers_registry(crawlers_file: Path) -> dict[str, type[Crawler]]:
    """Load CRAWLERS list from the given crawlers file."""
    if not crawlers_file.exists():
        print(
            f"Error: '{crawlers_file}' not found.\n"
            f"Create a '{crawlers_file.name}' file with a CRAWLERS list. Example:\n"
            f"\n"
            f"  from myproject.quotes_crawler import QuotesToScrapeCrawler\n"
            f"\n"
            f"  CRAWLERS = [QuotesToScrapeCrawler]"
        )
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("crawlers", crawlers_file)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    crawler_list: list[type[Crawler]] = getattr(module, "CRAWLERS", None)
    if crawler_list is None:
        print(f"Error: '{crawlers_file}' must define a 'CRAWLERS' list.")
        sys.exit(1)

    return {crawler.crawler_name: crawler for crawler in crawler_list}


def _parse_extra_kwargs(remaining: list[str]) -> dict[str, str]:
    """Convert ['-key', 'value', '--flag'] style args into a dict."""
    kwargs: dict[str, str] = {}
    i = 0
    while i < len(remaining):
        token = remaining[i]
        if token.startswith("-"):
            key = token.lstrip("-")
            if i + 1 < len(remaining) and not remaining[i + 1].startswith("-"):
                kwargs[key] = remaining[i + 1]
                i += 2
            else:
                kwargs[key] = "true"
                i += 1
        else:
            i += 1
    return kwargs


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="turbocrawler",
        description="TurboCrawler CLI — run any registered crawler by name.",
    )
    parser.add_argument(
        "crawler_name",
        help="The crawler_name attribute of the crawler to run (e.g. QuotesToScrape).",
    )
    parser.add_argument(
        "--crawlers-file",
        default=CRAWLERS_FILE,
        help=f"Path to the file that defines the CRAWLERS list (default: {CRAWLERS_FILE}).",
    )

    args, remaining = parser.parse_known_args()
    cli_kwargs = _parse_extra_kwargs(remaining)

    cwd = Path.cwd()
    if str(cwd) not in sys.path:
        sys.path.insert(0, str(cwd))

    crawlers_path = Path(args.crawlers_file)
    if not crawlers_path.is_absolute():
        crawlers_path = cwd / crawlers_path

    crawlers = _load_crawlers_registry(crawlers_path)

    if args.crawler_name not in crawlers:
        available = ", ".join(crawlers.keys()) if crawlers else "none found"
        print(f"Error: crawler '{args.crawler_name}' not found.")
        print(f"Available crawlers: {available}")
        sys.exit(1)

    crawler_class = crawlers[args.crawler_name]
    asyncio.run(CrawlerRunner(crawler=crawler_class, cli_kwargs=cli_kwargs).run())


if __name__ == "__main__":
    main()
