#!/usr/bin/env python

import click
import sys
from bantool.bantool import Bantool
from bantool.config import download_banlist
from bantool.config import init_config

import logging

logger = logging.getLogger("bantool")

def init_files():
    click.echo("Initalizing config files.")
    init_config("config.json")
    click.echo("Downloading banlist")
    download_banlist("namelist.txt")

@click.command()
@click.option("--init", "-i", "do_init", is_flag=True)
@click.option("--config", default="config.json", type=str)
def main(do_init, config):
    if do_init:
        init_files()
        sys.exit(0)
    try:
        tool = Bantool(config=config)
        tool.run()
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

# __END__
