#!/usr/bin/env python3
"""
Class representing a single Browser window.
"""

import _thread
import glob
import os
import sys
import time
from typing import Generator, List

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


class Browser:
    """Represents a single window for running Twitch chat commands."""

    status: str
    profile_name: str
    profile: webdriver.FirefoxProfile
    thread_lock: _thread
    userlist: str
    index: int
    channel: str
    command_list: list

    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.profile = self.setup_profile()

    def setup_profile(self):
        profile = webdriver.FirefoxProfile(self.profile_name)
        profile.set_preference(
            "security.insecure_field_warning.contextual.enabled", False
        )
        profile.set_preference("security.enterprise_roots.enabled", True)
        options = Options()
        if self.index != 0 and self.headless_mode:
            options.add_argument("--headless")
        return profile

    def yield_chunks(n: int, lst: list) -> Generator[list, None, None]:
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            end = i + n
            yield lst[i:end]

    def run(self, index: int, command_list: list):
        self.browser_status[index] = "Starting"
        try:
            with open(userlist, "r") as _namelist:
                _namelist_stripped = sorted(map(str.strip, _namelist.readlines()))
            chunked_lists = self.yield_chunks(_namelist_stripped, self.chunk_size)
            with webdriver.Firefox(
                options=options,
                executable_path="FirefoxPortable/App/Firefox64/geckodriver.exe",
                firefox_profile=profile,
                firefox_binary="FirefoxPortable/App/Firefox64/firefox.exe",
            ) as driver:
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
                    presence_of_element_located((By.CSS_SELECTOR, CHAT_CSS_SELECTOR))
                )
                chat_welcome_message = wait.until(
                    presence_of_element_located((By.CSS_SELECTOR, ".chat-line__status"))
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
                        for chunk in chunked_lists:
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
