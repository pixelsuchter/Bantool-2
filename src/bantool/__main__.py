#!/usr/bin/env python

import click
from bantool.bantool import Bantool
from bantool.config import download_banlist
from bantool.config import init_config


@click.command()
@click.option("--init", "-i", "do_init", is_flag=True)
@click.option("--config", default="config.json", type=str)
@click.option("--banlist", default="namelist.txt", type=str)
@click.option()
def main(do_init, config, banlist):
    if do_init:
        print("Initalizing config files")
        init_config(config)
        print("Downloading banlist")
        download_banlist(banlist)
    else:
        tool = Bantool()
        tool.run()


if __name__ == "__main__":
    main()

# __END__
