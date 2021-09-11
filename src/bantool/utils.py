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

def split_files(channel: str, outprefix: str):
    # File creation
    lists_dir = pathlib.Path("banned_lists/")
    streamer_banned_file = lists_dir / pathlib.Path(f"{channel}.txt")
    if not lists_dir.exists():
        lists_dir.os.mkdir()
    if not streamer_banned_file.exists():
        streamer_banned_file.touch()

    # Cleanup Old Files
    self.delete_split_namelists()
    with open(self.namelist, "r") as namelist, open(
        streamer_banned_file, "r"
    ) as banned_names:
        _nameset = set([line.strip() for line in namelist])
        _banned_set = set([line.strip() for line in banned_names])
    logger.info("Creating difference for %s", channel)
    difference_to_ban = sorted(_nameset.difference(_banned_set))

    # preparing the banlistlist files
    split_banlists = []
    num_of_files_to_create = max(
        min(len(difference_to_ban) // self.names_per_file, self.num_windows),
        1,
    )
    # Split banlist based on available threads
    self.browser_status = [
        "Not Started"
    ] * num_of_files_to_create  # update status lists
    self.counter = [0] * num_of_files_to_create  # update status lists
    logger.info("Creating %d files", num_of_files_to_create)
    for i in range(num_of_files_to_create):
        f = open(f"{outprefix}_namelist_split{i}.txt", "w")
        split_banlists.append(f)
    for idx, name in enumerate(difference_to_ban):
        split_banlists[idx % num_of_files_to_create].write(f"{name}\n")
    for file in split_banlists:
        file.close()