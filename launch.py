from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler

import scraper


def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart)
    crawler.start()

    print("\nTop 50 words:")
    scraper.print_top_50()
    print(f"\nNumber of unique pages: {scraper.number_of_unique_pages()}")
    scraper.longest_page()   
    print("\nSubdomain breakdown:")
    subdomains = scraper.get_subdomains()
    for host, i in sorted(subdomains.items()):
        print(f"{host}, {i}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)
