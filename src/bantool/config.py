#!/usr/bin/env python3

import json
from typing import List, NamedTuple
import stringcase as sc


class ConfigNT(NamedTuple):
    twitch_channels: List[str]
    account_name: str
    number_of_browser_windows: int
    firefox_profile: str
    block: bool
    ban: bool
    unban: bool
    unblock: bool
    greeting_emote: str
    chunk_size: int
    namelist: str


def load_config_to_dict(config_path: str) -> dict:
    with open(config_path) as cfg:
        config = dict(json.load(cfg))

    processed = {
        sc.snakecase(k.lower()): v
        for k, v in config.items()
    }

    return processed
