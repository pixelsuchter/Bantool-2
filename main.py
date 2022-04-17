import _thread
import glob
import json
import os
import shutil
import subprocess
import sys
import time

import colorama
from selenium.webdriver import ActionChains

chat_css_selector = "[role='textbox']"
rules_window_accept_css_selector = ".kLnQWs"

colorama.init()
try:
    from selenium.common.exceptions import *
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
    from selenium.webdriver.support.expected_conditions import presence_of_element_located
except ImportError:
    # installs selenium module if it is missing, needed for browser control
    print('Installing selenium')
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    print('Installing colorama')
    subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
    print('Installing pyperclip')
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyperclip"])
    from selenium.common.exceptions import *
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
    from selenium.webdriver.support.expected_conditions import presence_of_element_located

try:
    from tqdm import tqdm
except ImportError:
    # installs tqdm module if it is missing
    print('Installing tqdm')
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm

class Bantool:
    def __init__(self):
        self.config = dict()
        self.browser_status = ["Not Started"]
        self.all_browsers_ready = False
        self.counter = [0]
        self.channels = [""]
        self.account_name = None
        self.num_windows = 0
        self.names_per_file = 1000
        self.headless_mode = False
        self.do_ban = False
        self.do_block = False
        self.do_unban = False
        self.do_unblock = False
        # self.greeting_emote = ""
        self.thread_lock = _thread.allocate_lock()
        self.browser_lock = _thread.allocate_lock()

    def load_config(self):
        try:
            with open("config.json", "r") as cfg:
                self.config = json.load(cfg)
                assert type(self.config["twitch_channels"]) == list
                assert type(self.config["account_name"]) == str
                assert type(self.config["Number_of_browser_windows"]) == int
                assert type(self.config["Firefox_profile"]) == str
                assert type(self.config["Block"]) == bool
                assert type(self.config["Ban"]) == bool
                assert type(self.config["Unban"]) == bool
                assert type(self.config["Unblock"]) == bool
            self.channels = self.config["twitch_channels"]
            self.account_name = self.config["account_name"]
            self.num_windows = self.config["Number_of_browser_windows"]
            self.do_ban = self.config["Ban"]
            self.do_block = self.config["Block"]
            self.do_unban = self.config["Unban"]
            self.do_unblock = self.config["Unblock"]
        except (OSError, json.JSONDecodeError, AssertionError, KeyError) as e:
            print("Config file does not exist or corrupt, creating default config\n")
            if os.path.isfile("config.json"):
                if os.path.isfile("config.json.broken"):
                    os.remove("config.json.broken")
                os.rename("config.json", "config.json.broken")
            with open("config.json", "w") as f:
                config = {"twitch_channels": [""], "account_name": "", "Number_of_browser_windows": 1, "Firefox_profile": "", "Block": True, "Ban": True, "Unban": True,
                          "Unblock": True, "Greeting Emote": "", "Chunk size": 1000}
                json.dump(config, f, sort_keys=True, indent=4)

    def check_files(self):
        if not os.path.isfile("namelist.txt"):
            print("Namelist does not exist, creating file. Please insert names and restart")
            with open("namelist.txt", "x"):
                pass
            input("Press enter to exit")
            exit(0)

        if self.channels == [""] or not self.account_name or not self.num_windows or not self.config["Firefox_profile"]:
            print("Config not set correctly")
            input("Press enter to exit")
            exit(0)

    def sort_file_and_dedupe(self, filename: str):
        with open(filename, "r") as file:
            namelist = file.readlines()
            name_set = set()
            for name in namelist:
                _name = name.strip().lower()
                if _name:
                    name_set.add(_name)
        with open(filename, "w") as file:
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
            with open("namelist.txt", "r") as namelist:
                # File creation
                if not os.path.isdir("banned_lists"):  # create folder if nescessary
                    os.mkdir("banned_lists")
                if not os.path.isfile("banned_lists/{streamer}.txt".format(streamer=channel)):  # create streamer specific file if non existant
                    with open("banned_lists/{streamer}.txt".format(streamer=channel), "x"):
                        pass
                self.delete_split_namelists()

                # Calculating names to ban
                with open("banned_lists/{streamer}.txt".format(streamer=channel), "r") as banned_names:
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
                    num_of_files_to_create = max(min(len(difference_to_ban) // self.names_per_file, self.num_windows), 1)
                    self.browser_status = ["Not Started"] * num_of_files_to_create  # update status lists
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
        if self.config["Unban"] or self.config["Unblock"]:
            with open("namelist.txt", "r") as namelist:
                # File creation
                if not os.path.isdir("banned_lists"):  # create folder if nescessary
                    os.mkdir("banned_lists")
                if not os.path.isfile("banned_lists/{streamer}.txt".format(streamer=channel)):  # create streamer specific file if non existant
                    with open("banned_lists/{streamer}.txt".format(streamer=channel), "x"):
                        pass
                self.delete_split_namelists()

                # Calculating names to unban
                with open("banned_lists/{streamer}.txt".format(streamer=channel), "r") as banned_names:
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
                        num_of_files_to_create = max(min(len(difference_to_unban) // self.names_per_file, self.num_windows), 1)
                        self.browser_status = ["Not Started"] * num_of_files_to_create  # update status lists
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
        _lock = self.browser_lock  # cached reference to avoid repeated self lookups

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        try:
            with open(userlist, "r") as _namelist:
                if len(_namelist.readlines()) > 0:
                    self.browser_status[index] = "Starting"
                    _namelist.seek(0)
                    _namelist_stripped = sorted(map(str.strip, _namelist.readlines()))
            self.thread_lock.acquire()
            profile = webdriver.FirefoxProfile(self.config["Firefox_profile"])
            profile.set_preference("security.insecure_field_warning.contextual.enabled", False)
            profile.set_preference("security.enterprise_roots.enabled", True)
            options = Options()
            if index != 0 and self.headless_mode:
                options.add_argument('--headless')
            with webdriver.Firefox(options=options, executable_path="FirefoxPortable/App/Firefox64/geckodriver.exe", firefox_profile=profile,
                                   firefox_binary="FirefoxPortable/App/Firefox64/firefox.exe") as driver:
                # driver.minimize_window()
                self.thread_lock.release()
                # print(driver.profile.profile_dir)
                driver.set_window_size(1000, 1000)
                wait = WebDriverWait(driver, 120)
                wait_rules = WebDriverWait(driver, 5)
                driver.get("https://www.twitch.tv/popout/{channel}/chat".format(channel=channel))
                chat_field = wait.until(presence_of_element_located((By.CSS_SELECTOR, chat_css_selector)))
                chat_welcome_message = wait.until(presence_of_element_located((By.CSS_SELECTOR, ".chat-line__status")))
                time.sleep(1)
                if chat_field.is_displayed():
                    action = ActionChains(driver)
                    action.move_to_element(chat_field).click().perform()

                if chat_field.is_displayed():
                    self.browser_status[index] = "Ready"
                    while not self.all_browsers_ready:
                        time.sleep(0.1)
                    _sub_lists = chunks(_namelist_stripped, 200)
                    for _sub_list in _sub_lists:
                        for i in range(1, 5):  # retry if the script times out
                            try:
                                for name in _sub_list:
                                    for command in command_list:
                                        driver.find_element(By.CSS_SELECTOR, chat_css_selector).send_keys((command + " " + name)[::-1] + Keys.ENTER)
                                        # time.sleep(0.1) # added to prevent timeout, doesn't work :(

                                with self.thread_lock:  # this is really bad....
                                    if "/ban" in command_list or "/block" in command_list:
                                        with open(f"banned_lists/{channel}.txt", "a") as banlist:
                                            banlist.writelines("".join([f"{_name}\n" for _name in _sub_list]))
                                    elif "/unban" in command_list or "/unblock" in command_list:
                                        with open(f"banned_lists/{channel}.txt", "r") as banlist:
                                            old_bannedlist = set(map(str.strip, banlist.readlines()))
                                        unbanned_names = set(_sub_list)
                                        new_banned_list = old_bannedlist.difference(unbanned_names)
                                        new_banned_list = list(set([f"{name}\n" for name in new_banned_list]))
                                        with open(f"banned_lists/{channel}.txt", "w") as banlist:
                                            for name in sorted(new_banned_list):
                                                banlist.write(name)

                                self.counter[index] += len(_sub_list)

                                break
                            except Exception as e:
                                print(e)
                                print(f"failed attemt {i} out of 5")
                        else:
                            print("failed all 5 attemts, restart is reccomended")
                time.sleep(1)
        except LookupError as e:
            print(e)
            print("couldn't start instance {}".format(index))
        finally:
            self.browser_status[index] = "Done"
            time.sleep(1)  # used to prevent missing last name in short lists

    def start_browsers_ban(self, channel):
        self.all_browsers_ready = False

        def _cleanup_banfiles():
            part_files = glob.glob("banned_part*.txt")
            with open("banned_lists/{streamer}.txt".format(streamer=channel), "r") as banlist:
                old_list = set(map(str.strip, banlist.readlines()))
                for _filePath in part_files:
                    with open(_filePath, "r") as part_file:
                        old_list.update(set(part_file.readlines()))
                    os.remove(_filePath)
                old_list = [f"{name}\n" for name in sorted(old_list)]
            with open("banned_lists/{streamer}.txt".format(streamer=channel), "w") as banlist:
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
                    _thread.start_new_thread(self.browser, (namelist, idx, channel, commands))
                    # time.sleep(2)  # No longer needed due to threads blocking simultaneous profile access
                    pass
            else:
                _cleanup_banfiles()
                return  # Nothing to do
            print("\n")
            colorama.init(autoreset=True)
            fore = colorama.Fore
            i = 0
            while "Not Started" in self.browser_status or "Starting" in self.browser_status:
                if i == 0:
                    print(f"\rWaiting for Browsers [{fore.RED}•{fore.RESET}     ]", end="")
                    i += 1
                    time.sleep(0.3)
                elif i == 1 or i == 9:
                    print(f"\rWaiting for Browsers [ {fore.YELLOW}•{fore.RESET}    ]", end="")
                    i += 1
                    time.sleep(0.3)
                elif i == 2 or i == 8:
                    print(f"\rWaiting for Browsers [  {fore.GREEN}•{fore.RESET}   ]", end="")
                    i += 1
                    time.sleep(0.3)
                elif i == 3 or i == 7:
                    print(f"\rWaiting for Browsers [   {fore.CYAN}•{fore.RESET}  ]", end="")
                    i += 1
                    time.sleep(0.3)
                elif i == 4 or i == 6:
                    print(f"\rWaiting for Browsers [    {fore.BLUE}•{fore.RESET} ]", end="")
                    i += 1
                    time.sleep(0.3)
                elif i == 5:
                    print(f"\rWaiting for Browsers [     {fore.MAGENTA}•{fore.RESET}]", end="")
                    i += 1
                    time.sleep(0.3)
                else:
                    i = 0
            self.all_browsers_ready = True
            start = time.time()
            progressbar = tqdm(total=num_names, unit=" Names", file=sys.stdout, colour="#0FEED0", ascii=True, desc="Banning")
            old_sum = 0
            new_sum = sum(self.counter)
            while "Ready" in self.browser_status:
                old_sum = new_sum
                new_sum = sum(self.counter)
                progressbar.update(new_sum - old_sum)
                time.sleep(0.01)
            progressbar.close()
            print("Done")
            _cleanup_banfiles()

    def start_browsers_unban(self, channel):
        self.all_browsers_ready = False

        def _cleanup_unban_files():
            part_files = glob.glob("banned_part*.txt")
            with open("banned_lists/{streamer}.txt".format(streamer=channel), "r") as banlist:
                old_bannedlist = set(map(str.strip, banlist.readlines()))
                unbanned_names = set()
                for _filePath in part_files:
                    with open(_filePath, "r") as part_file:
                        unbanned_names.update(set(map(str.strip, part_file.readlines())))
                    os.remove(_filePath)
                banlist.seek(0)
                new_banned_list = old_bannedlist.difference(unbanned_names)
                new_banned_list = list(set([f"{name}\n" for name in new_banned_list]))
            with open("banned_lists/{streamer}.txt".format(streamer=channel), "w") as banlist:
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
                    _thread.start_new_thread(self.browser, (namelist, idx, channel, ["/unban"]))
                    # time.sleep(2)  # No longer needed due to threads blocking simultaneous profile access
            else:  # Nothing to do
                _cleanup_unban_files()
                return
            print("\n")
            colorama.init(autoreset=True)
            fore = colorama.Fore
            i = 0
            while "Not Started" in self.browser_status or "Starting" in self.browser_status:
                if i == 0:
                    print(f"\rWaiting for Browsers [{fore.RED}•{fore.RESET}     ]", end="")
                    i += 1
                    time.sleep(0.3)
                elif i == 1 or i == 9:
                    print(f"\rWaiting for Browsers [ {fore.YELLOW}•{fore.RESET}    ]", end="")
                    i += 1
                    time.sleep(0.3)
                elif i == 2 or i == 8:
                    print(f"\rWaiting for Browsers [  {fore.GREEN}•{fore.RESET}   ]", end="")
                    i += 1
                    time.sleep(0.3)
                elif i == 3 or i == 7:
                    print(f"\rWaiting for Browsers [   {fore.CYAN}•{fore.RESET}  ]", end="")
                    i += 1
                    time.sleep(0.3)
                elif i == 4 or i == 6:
                    print(f"\rWaiting for Browsers [    {fore.BLUE}•{fore.RESET} ]", end="")
                    i += 1
                    time.sleep(0.3)
                elif i == 5:
                    print(f"\rWaiting for Browsers [     {fore.MAGENTA}•{fore.RESET}]", end="")
                    i += 1
                    time.sleep(0.3)
                else:
                    i = 0
            self.all_browsers_ready = True
            start = time.time()
            progressbar = tqdm(total=num_names, unit=" Names", file=sys.stdout, colour="#0FEED0", ascii=True, desc="Unbanning")
            old_sum = 0
            new_sum = sum(self.counter)
            while "Ready" in self.browser_status:
                old_sum = new_sum
                new_sum = sum(self.counter)
                progressbar.update(new_sum - old_sum)
                time.sleep(0.01)
            progressbar.close()
            print("Done")
            _cleanup_unban_files()

    def _clean_temporary_files(self):
        print("Cleaning temporary files")
        tempdir = os.path.expandvars(os.path.join("%LOCALAPPDATA%", "Temp"))
        print(f"Temp Folder is: {tempdir}")
        tempfolders = [tmp for tmp in os.listdir(tempdir) if tmp.startswith("rust_moz") or tmp.startswith("tmp")]
        for folder in tempfolders:
            shutil.rmtree(os.path.join(tempdir, folder))
        print("done cleaning temporary files")

    def run(self):
        self.load_config()
        self.check_files()
        self._clean_temporary_files()
        self.sort_file_and_dedupe("namelist.txt")
        for chnl in self.channels:
            self.split_unbanfiles(chnl)
            self.start_browsers_unban(chnl)
            self.split_banfiles(chnl)
            self.start_browsers_ban(chnl)
            self.delete_split_namelists()


if __name__ == "__main__":
    tool = Bantool()
    tool.run()
