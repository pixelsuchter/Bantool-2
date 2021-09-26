#!/usr/bin/env python

import requests
import json
import os.path
from typing import NamedTuple, List, Optional
import snakecase as sc

NAMELIST_URL = "https://github.com/LinoYeen/Namelists/raw/main/namelist.txt"

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

# FIXME: Investigate using namelist for requests if url


default_config = ConfigNT(
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
    namelist="namelist.txt",
)


def download_banlist(banlist_dir: str = ".", _url: str = NAMELIST_URL) -> str:
    """Downloads latest version of LinoYeen's banlist.

    Accepts:
        banlist_dir (Pathlike): Directory where namelist is downloaded
    Returns:
        path of downloaded banlist
    """
    r = requests.get(_url)

    banlist_dir = os.path.abspath(banlist_dir)
    if not os.path.isdir(banlist_dir):
        raise ValueError(f"{banlist_dir} is not a directory")
    banlist_path = os.path.join(banlist_dir, "namelist.txt")

    with open(banlist_path, 'wb') as fh:
        fh.write(r.content)
    return banlist_path


def init_config(config_file: str = "config.json") -> str:
    """Creates default config.

    Accepts:
        config_file (Pathlike): Path to new config file
    Returns:
        Same path to config file.
    Raises:
        None
    """
    with open(config_file, "w") as f:
        json.dump(default_config._asdict(), f, sort_keys=True, indent=4)
    return config_file


def load_config(config_path: str) -> ConfigNT:
    """Processes JSON config file to ConfigNT

    Accepts:
        config_path (str): Path to config
    Returns:
        parsed config NamedTuple
    Raises:
        ValueError: config file not found.
    """

    if not os.path.exists(config_path):
        raise ValueError(f"Could not find {config_path}")

    try:
        with open("config.json", "r") as cfg:
            config_dict: dict = json.load(cfg)
    except Exception as e:
        raise ValueError(e) from None
    # Normalize keys

    for k in config_dict.keys():
        # All lower, underscore delimited
        k_norm = sc.snakecase(k.lower().strip())
        if k == k_norm:
            # "Correct" key
            continue
        else:
            # Replace with normalized key
            config_dict[k_norm] = config_dict.pop(k)

    config = ConfigNT(**{k: v for k, v in config_dict.items() if k in ConfigNT._fields})
    """
    assert type(self.config["twitch_channels"]) == list
    assert type(self.config["account_name"]) == str
    assert type(self.config["Number_of_browser_windows"]) == int
    assert type(self.config["Firefox_profile"]) == str
    assert type(self.config["Block"]) == bool
    assert type(self.config["Ban"]) == bool
    assert type(self.config["Unban"]) == bool
    assert type(self.config["Unblock"]) == bool
    """

    return config


# __END__
