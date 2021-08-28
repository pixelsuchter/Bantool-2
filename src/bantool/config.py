#!/usr/bin/env python3

import os.path
import json
from typing import List, NamedTuple, TypedDict
import stringcase as sc
import logging

logger = logging.getLogger(__name__)


class ConfigDict(TypedDict):
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


default_dict: ConfigDict = dict(
    twitch_channels=[""],
    account_name="",
    number_of_browser_windows=1,
    firefox_profile="",
    block=True,
    ban=True,
    unban=True,
    unblock=True,
    greeting_emote="",
    chunk_size=1000,
    namelist="",
)


def create_default_config(config_path: str) -> str:
    with open(config_path, "w") as f:
        json.dump(default_dict, f, sort_keys=True, indent=4)
    return config_path


def load_config_to_dict(config_path: str) -> ConfigDict:
    if not os.path.exists(config_path):
        logging.error("Creating default config file: %s", config_path)
        config_path = create_default_config(config_path)

    with open(config_path) as cfg:
        config = dict(json.load(cfg))

    processed: ConfigDict = {sc.snakecase(k.lower()): v for k, v in config.items()}

    return processed
