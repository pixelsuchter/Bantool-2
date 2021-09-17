#!/usr/bin/env python

import requests
import json


def download_banlist(banlist_path: str = "namelist.txt"):
    """Download latest version of LinoYeen's banlist."""
    r = requests.get("https://github.com/LinoYeen/Namelists/raw/main/namelist.txt")
    with open(banlist_path, 'wb') as fh:
        fh.write(r.content)


def init_config(config_file: str = "config.json"):
    with open(config_file, "w") as f:
        config = {
            "twitch_channels": [""],
            "account_name": "",
            "Number_of_browser_windows": 1,
            "Firefox_profile": "",
            "Block": True,
            "Ban": True,
            "Unban": True,
            "Unblock": True,
            "Greeting Emote": "",
            "Chunk size": 1000,
        }
        json.dump(config, f, sort_keys=True, indent=4)
