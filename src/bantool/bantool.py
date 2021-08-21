#!/usr/bin/env python3

import _thread
import glob
import json
import os
import sys
import time
from typing import List

import colorama

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

import logging

from bantool.config import ConfigNT

logger = logging.getLogger(__name__)
CHAT_CSS_SELECTOR = "textarea.ScInputBase-sc-1wz0osy-0"
RULES_WINDOW_ACCEPT_CSS_SELECTOR = ".bTWzyW"


class Bantool:
    account_name: str
    channels: List[str]
    chunk_size: int
    profile: str
    do_ban: bool
    do_block: bool
    do_unban: bool
    do_unblock: bool
    greeting_emote: str
    num_windows: int
    namelist: str

    def __init__(self, config: ConfigNT):
        self.config = config._asdict()

        self.channels = config.twitch_channels
        self.account_name = config.account_name
        self.num_windows = config.number_of_browser_windows
        self.do_ban = config.ban
        self.do_block = config.block
        self.do_unban = config.unban
        self.do_unblock = config.unblock
        self.greeting_emote = config.greeting_emote
        self.chunk_size = config.chunk_size
        self.namelist = config.namelist
        self.profile = config.firefox_profile

        self.browser_status = ["Not Started"]
        self.all_browsers_ready = False
        self.counter = [0]

        self.thread_lock = _thread.allocate_lock()
        try:
            self.check_config()
        except AssertionError as e:
            # Repackage assertion error
            raise ValueError(str(e)) from None

    def check_config(self):
        if not os.path.isfile(self.namelist):
            logger.error("Namelist not found: %s.", self.namelist)

        assert self.channels is not [""], "Channel(s) required"
        assert self.account_name, "Account name required"
        assert self.num_windows, "Number of windows required"
        assert self.profile, "Firefox profile required"

    def delete_split_namelists(self):
        namelist_files = glob.glob("ban_namelist_split*.txt")
        for filePath in namelist_files:
            try:
                os.remove(filePath)
            except OSError:
                print("Error while deleting file : ", filePath)
        namelist_files = glob.glob("unban_namelist_split*.txt")
        for filePath in namelist_files:
            try:
                os.remove(filePath)
            except OSError:
                print("Error while deleting file : ", filePath)

    def split_banfiles(self, channel):
        with open("namelist.txt", "r") as namelist:
            # File creation
            if not os.path.isdir("banned_lists"):  # create folder if nescessary
                os.mkdir("banned_lists")
            if not os.path.isfile(
                "banned_lists/{streamer}.txt".format(streamer=channel)
            ):  # create streamer specific file if non existant
                with open("banned_lists/{streamer}.txt".format(streamer=channel), "x"):
                    pass
            self.delete_split_namelists()

            # Calculating names to ban
            with open(
                "banned_lists/{streamer}.txt".format(streamer=channel), "r"
            ) as banned_names:
                # _nameset = set(sorted(namelist.readlines()))
                _nameset = set(map(str.strip, namelist.readlines()))
                _banned_set = set(map(str.strip, banned_names.readlines()))
                print("Creating difference for {streamer}".format(streamer=channel))
                start = time.time()
                difference_to_ban = sorted(_nameset.difference(_banned_set))
                end = time.time()
                print("Creating difference took {:.4f}s".format(end - start))

                # preparing the banlistlist files
                split_banlists = []
                num_of_files_to_create = max(
                    min(
                        len(difference_to_ban) // self.names_per_file, self.num_windows
                    ),
                    1,
                )
                self.browser_status = [
                    "Not Started"
                ] * num_of_files_to_create  # update status lists
                self.counter = [0] * num_of_files_to_create  # update status lists
                if num_of_files_to_create > 0:
                    for i in range(num_of_files_to_create):
                        f = open("ban_namelist_split{num}.txt".format(num=i), "w")
                        split_banlists.append(f)
                    for idx, name in enumerate(difference_to_ban):
                        split_banlists[idx % num_of_files_to_create].write(f"{name}\n")
                    for file in split_banlists:
                        file.close()

    def split_unbanfiles(self, channel):
        with open("namelist.txt", "r") as namelist:
            # File creation
            if not os.path.isdir("banned_lists"):  # create folder if nescessary
                os.mkdir("banned_lists")
            if not os.path.isfile(
                "banned_lists/{streamer}.txt".format(streamer=channel)
            ):  # create streamer specific file if non existant
                with open("banned_lists/{streamer}.txt".format(streamer=channel), "x"):
                    pass
            self.delete_split_namelists()

            # Calculating names to unban
            with open(
                "banned_lists/{streamer}.txt".format(streamer=channel), "r"
            ) as banned_names:
                _nameset = set(namelist.readlines())
                _banned_set = set(banned_names.readlines())
                print("Creating difference for {streamer}".format(streamer=channel))
                start = time.time()
                difference_to_unban = sorted(_banned_set.difference(_nameset))
                end = time.time()
                print("Creating difference took {:.4f}s".format(end - start))

                if difference_to_unban:
                    # preparing the unbanlist files
                    split_unbanlists = []
                    num_of_files_to_create = max(
                        min(
                            len(difference_to_unban) // self.names_per_file,
                            self.num_windows,
                        ),
                        1,
                    )
                    self.browser_status = [
                        "Not Started"
                    ] * num_of_files_to_create  # update status lists
                    self.counter = [0] * num_of_files_to_create  # update status lists
                    if num_of_files_to_create > 0:
                        for i in range(num_of_files_to_create):
                            f = open("unban_namelist_split{num}.txt".format(num=i), "w")
                            split_unbanlists.append(f)
                        for idx, name in enumerate(difference_to_unban):
                            split_unbanlists[idx % num_of_files_to_create].write(name)
                        for file in split_unbanlists:
                            file.close()

    def browser(self, userlist, index, channel, command_list):
        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                end = i + n
                yield lst[i:end]

        try:
            with open(userlist, "r") as _namelist:
                if len(_namelist.readlines()) > 0:
                    self.browser_status[index] = "Starting"
                    _namelist.seek(0)
                    _namelist_stripped = sorted(map(str.strip, _namelist.readlines()))
            chunked_lists = chunks(_namelist_stripped, self.chunk_size)
            for chunk in chunked_lists:
                self.thread_lock.acquire()
                profile = webdriver.FirefoxProfile(self.profile)
                profile.set_preference(
                    "security.insecure_field_warning.contextual.enabled", False
                )
                profile.set_preference("security.enterprise_roots.enabled", True)
                options = Options()
                if index != 0 and self.headless_mode:
                    options.add_argument('--headless')
                with webdriver.Firefox(
                    options=options,
                    executable_path="FirefoxPortable/App/Firefox64/geckodriver.exe",
                    firefox_profile=profile,
                    firefox_binary="FirefoxPortable/App/Firefox64/firefox.exe",
                ) as driver:
                    # print(driver.profile.profile_dir)
                    self.thread_lock.release()
                    driver.set_window_size(1000, 1000)
                    wait = WebDriverWait(driver, 120)
                    wait_rules = WebDriverWait(driver, 5)
                    driver.get(
                        "https://www.twitch.tv/popout/{channel}/chat".format(
                            channel=channel
                        )
                    )
                    chat_field = wait.until(
                        presence_of_element_located(
                            (By.CSS_SELECTOR, CHAT_CSS_SELECTOR)
                        )
                    )
                    chat_welcome_message = wait.until(
                        presence_of_element_located(
                            (By.CSS_SELECTOR, ".chat-line__status")
                        )
                    )
                    time.sleep(1)
                    if chat_field.is_displayed():
                        chat_field.click()
                    try:  # remove rules window
                        rules_button = wait_rules.until(
                            presence_of_element_located(
                                (By.CSS_SELECTOR, RULES_WINDOW_ACCEPT_CSS_SELECTOR)
                            )
                        )
                        if rules_button.is_displayed():
                            rules_button.click()
                    except (NoSuchElementException, TimeoutException):
                        pass
                    if chat_field.is_displayed():
                        chat_field.click()
                        chat_field = wait.until(
                            presence_of_element_located(
                                (By.CSS_SELECTOR, CHAT_CSS_SELECTOR)
                            )
                        )
                        chat_field.send_keys(
                            f"{self.greeting_emote} {index} {self.greeting_emote}",
                            Keys.ENTER,
                        )
                        self.browser_status[index] = "Ready"
                        while not self.all_browsers_ready:
                            time.sleep(0.1)
                        with open(
                            "banned_part{index}.txt".format(index=index), "w"
                        ) as banned_names:
                            for _name in chunk:
                                try:
                                    for command in command_list:
                                        chat_field = wait.until(
                                            presence_of_element_located(
                                                (By.CSS_SELECTOR, CHAT_CSS_SELECTOR)
                                            )
                                        )
                                        if command == "/ban":
                                            chat_field.send_keys(
                                                f"{command} {_name} Banned by bantool, if you think this was a mistake, please contact a moderator",
                                                Keys.ENTER,
                                            )
                                        else:
                                            chat_field.send_keys(
                                                f"{command} {_name}", Keys.ENTER
                                            )
                                    banned_names.write(f"{_name}\n")
                                    self.counter[index] += 1
                                except (
                                    ElementNotInteractableException,
                                    ElementClickInterceptedException,
                                ):
                                    try:  # remove rules window again, if nescessary
                                        rules_button = wait_rules.until(
                                            presence_of_element_located(
                                                (
                                                    By.CSS_SELECTOR,
                                                    RULES_WINDOW_ACCEPT_CSS_SELECTOR,
                                                )
                                            )
                                        )
                                        if rules_button.is_displayed():
                                            rules_button.click()
                                    except (NoSuchElementException, TimeoutException):
                                        pass
                with self.thread_lock:
                    with open(
                        "banned_lists/{streamer}.txt".format(streamer=channel), "a"
                    ) as banlist, open(
                        "banned_part{index}.txt".format(index=index), "r"
                    ) as banned_names:
                        _names = banned_names.readlines()
                        banlist.writelines(_names)
        except LookupError:
            print("couldn't start instance {}".format(index))
        finally:
            self.browser_status[index] = "Done"

    def start_browsers_ban(self, channel):
        self.all_browsers_ready = False

        def _cleanup_banfiles():
            part_files = glob.glob("banned_part*.txt")
            with open(
                "banned_lists/{streamer}.txt".format(streamer=channel), "r"
            ) as banlist:
                old_list = set(map(str.strip, banlist.readlines()))
                for _filePath in part_files:
                    with open(_filePath, "r") as part_file:
                        old_list.update(set(part_file.readlines()))
                    os.remove(_filePath)
                old_list = [f"{name}\n" for name in sorted(old_list)]
            with open(
                "banned_lists/{streamer}.txt".format(streamer=channel), "w"
            ) as banlist:
                for name in sorted(old_list):
                    banlist.write(name)

        # Banning
        num_names = 0
        split_banlists = glob.glob("ban_namelist_split*.txt")
        num_banlists = len(split_banlists)
        for filePath in split_banlists:
            with open(filePath, "r") as split_file:
                num_names += len(split_file.readlines())

        if num_names > 0:
            commands = []
            if self.do_ban:
                commands.append("/ban")
            if self.account_name == channel and self.do_block:
                commands.append("/block")
            if commands:
                print("Starting Browsers")
                for idx, namelist in enumerate(split_banlists):
                    _thread.start_new_thread(
                        self.browser, (namelist, idx, channel, commands)
                    )
                    # time.sleep(2)  # No longer needed due to threads blocking simultaneous profile access
                    pass
            else:
                _cleanup_banfiles()
                return  # Nothing to do
            print("\n")
            colorama.init(autoreset=True)
            fore = colorama.Fore
            i = 0
            while (
                "Not Started" in self.browser_status
                or "Starting" in self.browser_status
            ):
                if i == 0:
                    print(
                        f"\rWaiting for Browsers [{fore.RED}•{fore.RESET}     ]", end=""
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 1 or i == 9:
                    print(
                        f"\rWaiting for Browsers [ {fore.YELLOW}•{fore.RESET}    ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 2 or i == 8:
                    print(
                        f"\rWaiting for Browsers [  {fore.GREEN}•{fore.RESET}   ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 3 or i == 7:
                    print(
                        f"\rWaiting for Browsers [   {fore.CYAN}•{fore.RESET}  ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 4 or i == 6:
                    print(
                        f"\rWaiting for Browsers [    {fore.BLUE}•{fore.RESET} ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 5:
                    print(
                        f"\rWaiting for Browsers [     {fore.MAGENTA}•{fore.RESET}]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                else:
                    i = 0
            self.all_browsers_ready = True
            start = time.time()
            progressbar = tqdm(
                total=num_names,
                unit=" Names",
                file=sys.stdout,
                colour="#0FEED0",
                ascii=True,
                desc="Banning",
            )
            old_sum = 0
            new_sum = sum(self.counter)
            while "Ready" in self.browser_status:
                old_sum = new_sum
                new_sum = sum(self.counter)
                progressbar.update(new_sum - old_sum)
                # print("Progress: {prog:.2%}  Elapsed time: {elapsed}".format(prog=sum(self.counter) / num_names,
                #                                                              elapsed=str(datetime.timedelta(seconds=int(time.time() - start)))))
                time.sleep(0.01)
            progressbar.close()
            print("Done")
            _cleanup_banfiles()

    def start_browsers_unban(self, channel):
        self.all_browsers_ready = False

        def _cleanup_unban_files():
            part_files = glob.glob("banned_part*.txt")
            with open(
                "banned_lists/{streamer}.txt".format(streamer=channel), "r"
            ) as banlist:
                old_bannedlist = set(map(str.strip, banlist.readlines()))
                unbanned_names = set()
                for _filePath in part_files:
                    with open(_filePath, "r") as part_file:
                        unbanned_names.update(
                            set(map(str.strip, part_file.readlines()))
                        )
                    os.remove(_filePath)
                banlist.seek(0)
                new_banned_list = old_bannedlist.difference(unbanned_names)
                new_banned_list = list(set([f"{name}\n" for name in new_banned_list]))
            with open(
                "banned_lists/{streamer}.txt".format(streamer=channel), "w"
            ) as banlist:
                for name in sorted(new_banned_list):
                    banlist.write(name)

        # Unbanning
        num_names = 0
        split_banlists = glob.glob("unban_namelist_split*.txt")
        num_banlists = len(split_banlists)
        for filePath in split_banlists:
            with open(filePath, "r") as split_file:
                num_names += len(split_file.readlines())

        if num_names > 0:
            start = time.time()
            commands = []
            if self.do_unban:
                commands.append("/unban")
            if self.account_name == channel and self.do_unblock:
                commands.append("/unblock")
            if commands:
                for idx, namelist in enumerate(split_banlists):
                    _thread.start_new_thread(
                        self.browser, (namelist, idx, channel, ["/unban"])
                    )
                    # time.sleep(2)  # No longer needed due to threads blocking simultaneous profile access
            else:  # Nothing to do
                _cleanup_unban_files()
                return
            print("\n")
            colorama.init(autoreset=True)
            fore = colorama.Fore
            i = 0
            while (
                "Not Started" in self.browser_status
                or "Starting" in self.browser_status
            ):
                if i == 0:
                    print(
                        f"\rWaiting for Browsers [{fore.RED}•{fore.RESET}     ]", end=""
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 1 or i == 9:
                    print(
                        f"\rWaiting for Browsers [ {fore.YELLOW}•{fore.RESET}    ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 2 or i == 8:
                    print(
                        f"\rWaiting for Browsers [  {fore.GREEN}•{fore.RESET}   ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 3 or i == 7:
                    print(
                        f"\rWaiting for Browsers [   {fore.CYAN}•{fore.RESET}  ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 4 or i == 6:
                    print(
                        f"\rWaiting for Browsers [    {fore.BLUE}•{fore.RESET} ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 5:
                    print(
                        f"\rWaiting for Browsers [     {fore.MAGENTA}•{fore.RESET}]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                else:
                    i = 0
            self.all_browsers_ready = True
            start = time.time()
            progressbar = tqdm(
                total=num_names,
                unit=" Names",
                file=sys.stdout,
                colour="#0FEED0",
                ascii=True,
                desc="Unbanning",
            )
            old_sum = 0
            new_sum = sum(self.counter)
            while "Ready" in self.browser_status:
                old_sum = new_sum
                new_sum = sum(self.counter)
                progressbar.update(new_sum - old_sum)
                # print("Progress: {prog:.2%}  Elapsed time: {elapsed}".format(prog=sum(self.counter) / num_names,
                #                                                              elapsed=str(datetime.timedelta(seconds=int(time.time() - start)))))
                time.sleep(0.01)
            progressbar.close()
            print("Done")
            _cleanup_unban_files()

    def run(self):
        for chnl in self.channels:
            self.split_banfiles(chnl)
            self.start_browsers_ban(chnl)
            self.split_unbanfiles(chnl)
            self.start_browsers_unban(chnl)
            self.delete_split_namelists()
