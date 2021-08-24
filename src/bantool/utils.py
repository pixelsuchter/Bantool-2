#!/usr/bin/env python3

import pathlib
import os


def sort_file_and_dedupe(filename: str) -> str:
    with open(filename, "w+") as file:
        namelist = file.readlines()
        name_set = set()
        for name in namelist:
            _name = name.strip().lower()
            if _name:
                name_set.add(_name)
        file.seek(0)
        sorted_names = sorted(name_set)
        for _name in sorted_names:
            file.write(f"{_name}\n")
    return filename


def cleanup_files(streamer: str, prefix: str) -> None:
    part_files = pathlib.glob(f"{prefix}_part*.txt")
    banlist_path = os.path.join("banned_lists", f"{streamer}.txt")
    with open(banlist_path) as banlist:
        old_list = set(map(str.strip, banlist.readlines()))
        for _filePath in part_files:
            with open(_filePath, "r") as part_file:
                old_list.update(set(part_file.readlines()))
            os.remove(_filePath)
        old_list = [f"{name}\n" for name in sorted(old_list)]
    with open(banlist_path) as banlist:
        for name in sorted(old_list):
            banlist.write(name)


def cleanup_banfiles(streamer: str) -> None:
    cleanup_files(streamer, "banned")


def cleanup_unban_files(streamer: str):
    cleanup_files(streamer, "unbanned")
