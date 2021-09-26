#!/usr/bin/env python
import _thread
import glob
import os
import sys
import time
from typing import List, TYPE_CHECKING

from bantool.config import load_config
import colorama
import pyperclip as pc
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

if TYPE_CHECKING:
    from src.bantool.config import ConfigNT
colorama.init()
chat_css_selector = "textarea.ScInputBase-sc-1wz0osy-0"
rules_window_accept_css_selector = ".bTWzyW"

script = f"""
function Sleep(milliseconds) {{
  return new Promise(resolve => setTimeout(resolve, milliseconds));
}}

async function main(){{
    var names = ["hi", "there"];
    textbox = document.querySelector("{chat_css_selector}");
    chat_button = document.querySelector("div.brpYgf:nth-child(4) > button:nth-child(1)");
    for(let name of names){{
        console.info(textbox);
        textbox.chat_input = name; //todo doesn't work
        await Sleep(1000);  // test delay
        chat_button.click();
    }}
}}
main();
"""


class Bantool:
    config: 'ConfigNT'
    banlist: str
    channels: List[str]
    account_name: str
    num_windows: int
    firefox_profile: str
    do_block: bool = False
    do_ban: bool = False
    do_unban: bool = False
    do_unblock: bool = False
    greeting_emote: str
    chunk_size: int
    profile: str
    namelist: str
    temp_namelist: str = "temp_namelist.txt"

    def __init__(self, config: str):
        self.config: 'ConfigNT' = load_config(config)
        self.browser_status = ["Not Started"]
        self.all_browsers_ready = False
        self.counter = [0]
        self.names_per_file = 500
        self.headless_mode = False

        self.thread_lock = _thread.allocate_lock()
        self.browser_lock = _thread.allocate_lock()

        self.banlist = self.config.namelist
        self.channels = self.config.twitch_channels
        self.account_name = self.config.account_name
        self.num_windows = self.config.number_of_browser_windows
        self.profile = self.config.firefox_profile
        self.do_ban = self.config.ban
        self.do_block = self.config.block
        self.do_unban = self.config.unban
        self.do_unblock = self.config.unblock
        self.greeting_emote = self.config.greeting_emote
        self.chunk_size = self.config.chunk_size

    def check_files(self):
        if not os.path.isfile(self.temp_namelist):
            print(
                "Namelist does not exist, creating file. Please insert names and restart"
            )
            with open(self.temp_namelist, "x"):
                pass
            input("Press enter to exit")
            exit(0)

        if (
            self.channels == [""]
            or not self.account_name
            or not self.num_windows
            or not self.profile
        ):
            print("Config not set correctly")
            input("Press enter to exit")
            exit(0)

    def sort_file_and_dedupe(self):
        """Sort namelist to tempfile for running"""
        with open(self.banlist, "r") as file:
            namelist = file.readlines()
            name_set = set()
            for name in namelist:
                _name = name.strip().lower()
                if _name:
                    name_set.add(_name)
        with open(self.temp_namelist, "w") as file:
            sorted_Names = sorted(name_set)
            for _name in sorted_Names:
                file.write(f"{_name}\n")

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
        if self.config["Ban"] or self.config["Block"]:
            with open(self.temp_namelist, "r") as namelist:
                # File creation
                if not os.path.isdir("banned_lists"):  # create folder if nescessary
                    os.mkdir("banned_lists")
                if not os.path.isfile(
                    "banned_lists/{streamer}.txt".format(streamer=channel)
                ):  # create streamer specific file if non existant
                    with open(
                        "banned_lists/{streamer}.txt".format(streamer=channel), "x"
                    ):
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
                            len(difference_to_ban) // self.names_per_file,
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
                            f = open("ban_namelist_split{num}.txt".format(num=i), "w")
                            split_banlists.append(f)
                        for idx, name in enumerate(difference_to_ban):
                            split_banlists[idx % num_of_files_to_create].write(
                                f"{name}\n"
                            )
                        for file in split_banlists:
                            file.close()

    def split_unbanfiles(self, channel):
        if self.config["Unban"] or self.config["Unblock"]:
            with open(self.temp_namelist, "r") as namelist:
                # File creation
                if not os.path.isdir("banned_lists"):  # create folder if nescessary
                    os.mkdir("banned_lists")
                if not os.path.isfile(
                    "banned_lists/{streamer}.txt".format(streamer=channel)
                ):  # create streamer specific file if non existant
                    with open(
                        "banned_lists/{streamer}.txt".format(streamer=channel), "x"
                    ):
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
                        self.counter = [
                            0
                        ] * num_of_files_to_create  # update status lists
                        if num_of_files_to_create > 0:
                            for i in range(num_of_files_to_create):
                                f = open(
                                    "unban_namelist_split{num}.txt".format(num=i), "w"
                                )
                                split_unbanlists.append(f)
                            for idx, name in enumerate(difference_to_unban):
                                split_unbanlists[idx % num_of_files_to_create].write(
                                    name
                                )
                            for file in split_unbanlists:
                                file.close()

    def browser(self, userlist, index, channel, command_list):
        _lock = self.browser_lock  # cached reference to avoid repeated self lookups

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                j = i + n
                yield lst[i:j]

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
                            (By.CSS_SELECTOR, chat_css_selector)
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
                                (By.CSS_SELECTOR, rules_window_accept_css_selector)
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
                                (By.CSS_SELECTOR, chat_css_selector)
                            )
                        )
                        # chat_field.send_keys(f"{self.greeting_emote} {index} {self.greeting_emote}", Keys.ENTER)
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
                                                (By.CSS_SELECTOR, chat_css_selector)
                                            )
                                        )
                                        if command == "/ban":
                                            with _lock:
                                                pc.copy(str(f"{command} {_name}"))
                                                chat_field.send_keys(Keys.CONTROL, "v")
                                            chat_field.send_keys(Keys.ENTER)
                                        else:
                                            with _lock:
                                                pc.copy(str(f"{command} {_name}"))
                                                chat_field.send_keys(Keys.CONTROL, "v")
                                            chat_field.send_keys(Keys.ENTER)
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
                                                    rules_window_accept_css_selector,
                                                )
                                            )
                                        )
                                        if rules_button.is_displayed():
                                            rules_button.click()
                                    except (NoSuchElementException, TimeoutException):
                                        pass
                                # print(script)
                                # driver.execute_script(script)
                                # time.sleep(1000)
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
        self.load_config()
        self.check_files()
        self.sort_file_and_dedupe()
        for chnl in self.channels:
            self.split_banfiles(chnl)
            self.start_browsers_ban(chnl)
            self.split_unbanfiles(chnl)
            self.start_browsers_unban(chnl)
            self.delete_split_namelists()


# __END__
