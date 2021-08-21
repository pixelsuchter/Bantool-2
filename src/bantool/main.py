#!/usr/bin/env python3

from typing import List, Optional
from bantool.bantool import Bantool
from bantool.config import ConfigNT, load_config_to_dict
from bantool.utils import sort_file_and_dedupe
import argparse

import logging

logger = logging.getLogger("bantool")


def parse_args(argv: Optional[list] = None) -> ConfigNT:

    parser = argparse.ArgumentParser("bantool")

    config_group = parser.add_argument_group("config")
    config_group.add_argument(
        "--config", help="Path to JSON config. Values overridden by CLI"
    )

    cli_group = parser.add_argument_group()

    cli_group.add_argument("--channels", action="append", dest="twitch_channels")
    cli_group.add_argument("--account-name", metavar=str, help="Twitch account name")
    cli_group.add_argument(
        "--n-browser-windows", metavar=int, dest="number_of_browser_windows"
    )
    cli_group.add_argument(
        "--firefox-profile",
        dest="Firefox_profile",
        metavar=str,
        help="Name of new Firefox profile.",
    )
    cli_group.add_argument("--block", action="store_true", default=True)
    cli_group.add_argument("--unblock", action="store_true", default=True)
    cli_group.add_argument("--ban", action="store_true", default=True)
    cli_group.add_argument("--unban", action="store_true", default=True)
    cli_group.add_argument("--greeting-emote", metavar=str)
    cli_group.add_argument("--chunk-size", metavar=int, default=1000)
    cli_group.add_argument("--namelist", help="List of Twitch accounts, one per line.")

    if argv:
        args, unknown_args = parser.parse_known_args(argv)
    else:
        args, unknown_args = parser.parse_known_args()

    config_dict = {}
    if config := args.config:
        config_dict = load_config_to_dict(config)

    config_dict.update(dict(vars(args)))
    return ConfigNT(**{k: v for k, v in config_dict.items() if k in ConfigNT._fields()})


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    sort_file_and_dedupe(args.namelist)

    tool = Bantool(args)
    tool.run()


if __name__ == "__main__":
    main()
