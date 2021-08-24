#!/usr/bin/env python3

import argparse
import logging
import sys
from typing import List, Optional

from bantool.bantool import Bantool
from bantool.config import ConfigNT, load_config_to_dict
from bantool.utils import sort_file_and_dedupe

logger = logging.getLogger("bantool")


def parse_args(argv: Optional[list] = None) -> ConfigNT:

    parser = argparse.ArgumentParser("bantool")

    config_group = parser.add_argument_group("config")
    config_group.add_argument(
        "--config", help="Path to JSON config. Values overridden by CLI",
        default="config.json"
    )

    cli_group = parser.add_argument_group()

    cli_group.add_argument("--channels", action="append", dest="twitch_channels")
    cli_group.add_argument("--account-name", metavar=str, help="Twitch account name")
    cli_group.add_argument(
        "--n-browser-windows", metavar=int, dest="number_of_browser_windows"
    )
    cli_group.add_argument(
        "--firefox-profile",
        metavar=str,
        help="Name of new Firefox profile.",
    )
    cli_group.add_argument("--block", action="store_true", default=True)
    cli_group.add_argument("--unblock", action="store_true", default=True)
    cli_group.add_argument("--ban", action="store_true", default=True)
    cli_group.add_argument("--unban", action="store_true", default=True)
    cli_group.add_argument("--greeting-emote", metavar=str)
    cli_group.add_argument("--chunk-size", metavar=int)
    cli_group.add_argument(
        "--namelist", help="List of Twitch bots to ban, one per line."
    )

    if argv:
        args, unknown_args = parser.parse_known_args(argv)
    else:
        args, unknown_args = parser.parse_known_args()

    # Load config.json, creating with defaults if missing
    config_dict = {}
    if config := args.config:
        config_dict = load_config_to_dict(config)

    # Prepare dict of CLI args given
    args_dict = {
        k: v
        for k, v in dict(vars(args)).items()
        if v is not None
    }
    # Overwrite config file with given CLI args
    config_dict.update(args_dict)
    return ConfigNT(**{k: v for k, v in config_dict.items() if k in ConfigNT._fields})


def main(argv: Optional[List[str]] = None) -> None:
    exit_code = 0
    logger.info("Starting Bantool.")
    args = parse_args(argv)

    # Namelist contains names to ban
    # First sort and dedup names
    # Second split files into n, where n in # threads to use
    # Third initalize Browsers each with split ban list
    sort_file_and_dedupe(args.namelist)

    try:
        tool = Bantool(args)
        tool.run()
    except Exception as e:
        logger.exception(e)
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
