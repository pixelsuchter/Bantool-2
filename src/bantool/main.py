#!/usr/bin/env python3

from typing import Optional
from bantool.bantool import Bantool
from bantool.config import ConfigNT, load_config
import argparse

# from selenium.common.exceptions import *

import logging

logger = logging.getLogger("bantool")


def parse_args(argv: Optional[list] = None) -> ConfigNT:

    parser = argparse.ArgumentParser("bantool")

    mutex_group = parser.add_mutually_exclusive_group(required=True)
    mutex_group.add_argument("--config", help="Path to JSON config.")

    cli_group = mutex_group.add_argument_group("CLI")

    cli_group.add_argument("--channels", action="append", dest="twitch_channels")
    cli_group.add_argument("--account-name", metavar=str, help="Twitch account name")
    cli_group.add_argument("--n-browser-windows", metavar=int, dest="Number_of_browser_windows")
    cli_group.add_argument("--firefox-profile", dest="Firefox_profile", metavar=str, help="Name of new Firefox profile.")
    cli_group.add_argument("--block", action="store_true", metavar=bool, dest="Block", default=True)
    cli_group.add_argument("--unblock", action="store_true", metavar=bool, dest="Unblock", default=True)
    cli_group.add_argument("--ban", action="store_true", metavar=bool, dest="Ban", default=True)
    cli_group.add_argument("--unban", action="store_true", metavar=bool, dest="Unban", default=True)
    cli_group.add_argument("--greeting-emote", metavar=str)
    cli_group.add_argument("--chunk-size", metavar=int, default=1000)


    if argv:
        args, unknown_args = parser.parse_args(argv)
    else:
        args, unknown_args = parser.parse_args()
    if config := args.config:
        return load_config(config)

    args_dict = {k: v for k, v in vars(args).items() if k in ConfigNT._fields()}
    return ConfigNT(**args_dict)


def main() -> None:
    tool = Bantool()
    tool.run()


if __name__ == "__main__":
    main()
