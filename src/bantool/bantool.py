#!/usr/bin/env python3

import _thread
import glob
import os
import pathlib
import sys
import time
from typing import List

from rich import print

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

from bantool.utils import cleanup_banfiles, cleanup_unban_files
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

    def check_config(self) -> None:
        try:
            assert os.path.isfile(self.namelist), "Namelist not found."
            assert self.channels is not [""], "Channel(s) required"
            assert self.account_name, "Account name required"
            assert self.num_windows, "Number of windows required"
            assert self.profile, "Firefox profile required"
        except AssertionError as e:
            raise ValueError(str(e)) from None

    def delete_split_namelists(self):
        namelist_files = glob.glob("ban_namelist_split*.txt")
        for filePath in namelist_files:
            try:
                os.remove(filePath)
            except OSError:
                logger.error("Error while deleting file : ", filePath)
        namelist_files = glob.glob("unban_namelist_split*.txt")
        for filePath in namelist_files:
            try:
                os.remove(filePath)
            except OSError:
                logger.error("Error while deleting file : ", filePath)

    def split_files(self, channel: str, outprefix: str):
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

    def split_banfiles(self, channel: str):
        self.split_files(channel=channel, outprefix="ban")

    def split_unbanfiles(self, channel):
        self.split_files(channel=channel, outprefix="unban")

    def browser(self, userlist, index, channel, command_list):
        """
        Runs on each thread.
        """

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
                    options.add_argument("--headless")
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
            logger.error("couldn't start instance {}".format(index))
        finally:
            self.browser_status[index] = "Done"

    def start_browsers_ban(self, channel):

        self.all_browsers_ready = False

        # Banning
        num_names = 0
        split_banlists = pathlib.glob("ban_namelist_split*.txt")
        # This value is calculated when originally splitting files
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
                logger.info("Starting Browsers")
                for idx, namelist in enumerate(split_banlists):
                    _thread.start_new_thread(
                        self.browser, (namelist, idx, channel, commands)
                    )
                    pass
            else:
                cleanup_banfiles(channel)
                return  # Nothing to do
            print("\n")
            # Wait until broswers report back done
            i = 0
            while (
                "Not Started" in self.browser_status
                or "Starting" in self.browser_status
            ):
                if i == 0:
                    print(
                        "\rWaiting for Browsers []", end=""
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 1 or i == 9:
                    print(
                        "\rWaiting for Browsers [[red]•[/red]   ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 2 or i == 8:
                    print(
                        "\rWaiting for Browsers [  [green]•[/green]   ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 3 or i == 7:
                    print(
                        "\rWaiting for Browsers [   [cyan]•[/cyan]  ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 4 or i == 6:
                    print(
                        "\rWaiting for Browsers [    [blue]•[/blue] ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 5:
                    print(
                        "\rWaiting for Browsers [     [magenta]•[/magenta]]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                else:
                    i = 0
            self.all_browsers_ready = True
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
                time.sleep(0.01)
            progressbar.close()
            logger.info("Done")
            cleanup_banfiles(channel)

    def start_browsers_unban(self, channel):
        self.all_browsers_ready = False

        # Unbanning
        num_names = 0
        split_banlists = glob.glob("unban_namelist_split*.txt")
        for filePath in split_banlists:
            with open(filePath, "r") as split_file:
                num_names += len(split_file.readlines())

        if num_names > 0:
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
            else:  # Nothing to do
                cleanup_unban_files(channel)
                return
            print("\n")
            i = 0
            while (
                "Not Started" in self.browser_status
                or "Starting" in self.browser_status
            ):
                if i == 0:
                    print(
                        "\rWaiting for Browsers []", end=""
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 1 or i == 9:
                    print(
                        "\rWaiting for Browsers [[red]•[/red]   ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 2 or i == 8:
                    print(
                        "\rWaiting for Browsers [  [green]•[/green]   ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 3 or i == 7:
                    print(
                        "\rWaiting for Browsers [   [cyan]•[/cyan]  ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 4 or i == 6:
                    print(
                        "\rWaiting for Browsers [    [blue]•[/blue] ]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                elif i == 5:
                    print(
                        "\rWaiting for Browsers [     [magenta]•[/magenta]]",
                        end="",
                    )
                    i += 1
                    time.sleep(0.3)
                else:
                    i = 0
            self.all_browsers_ready = True
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
                time.sleep(0.01)
            progressbar.close()
            logger.info("Done")
            cleanup_unban_files(channel)

    def run(self):
        for chnl in self.channels:
            self.split_banfiles(chnl)
            self.start_browsers_ban(chnl)
            self.split_unbanfiles(chnl)
            self.start_browsers_unban(chnl)
            self.delete_split_namelists()