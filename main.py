import datetime
import json
import os
import subprocess
import sys
import time
import _thread
import glob

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
        self.done = [False]
        self.counter = [0]
        self.channels = [""]
        self.command = None
        self.num_windows = 0
        self.names_per_file = 500
        self.headless_mode = False

    def load_config(self):
        try:
            with open("config.json", "r") as cfg:
                self.config = json.load(cfg)
                assert type(self.config["twitch_channels"]) == list
                assert type(self.config["command"]) == str
                assert type(self.config["Number_of_browser_windows"]) == int
                assert type(self.config["Firefox_profile"]) == str
            self.channels = self.config["twitch_channels"]
            self.command = self.config["command"]
            self.num_windows = self.config["Number_of_browser_windows"]
        except (OSError, json.JSONDecodeError, AssertionError, KeyError) as e:
            print("Config file does not exist or corrupt, creating default config\n")
            if os.path.isfile("config.json"):
                if os.path.isfile("config.json.broken"):
                    os.remove("config.json.broken")
                os.rename("config.json", "config.json.broken")
            with open("config.json", "w") as f:
                config = {"twitch_channels": [""], "command": "/ban", "Number_of_browser_windows": 1, "Firefox_profile": ""}
                json.dump(config, f)


    def check_files(self):
        if not os.path.isfile("namelist.txt"):
            print("Namelist does not exist, creating file. Please insert names and restart")
            with open("namelist.txt", "x"):
                pass
            input("Press enter to exit")
            exit(0)

        if self.channels == [""] or not self.command or not self.num_windows or not self.config["Firefox_profile"]:
            print("Config not set correctly")
            input("Press enter to exit")
            exit(0)


    def delete_split_namelists(self):
        namelist_files = glob.glob("namelist_split*.txt")
        for filePath in namelist_files:
            try:
                os.remove(filePath)
            except OSError:
                print("Error while deleting file : ", filePath)


    def split_files(self, channel):
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
                _nameset = set(sorted(namelist.readlines()))
                _banned_set = set(sorted(banned_names.readlines()))
                print("Creating difference for {streamer}".format(streamer=channel))
                start = time.time()
                difference = _nameset.difference(_banned_set)
                end = time.time()
                print("Creating difference took {:.4f}s".format(end - start))

                # preparing the namelist files
                split_namelists = []
                num_of_files_to_create = max(min(len(difference) // self.names_per_file, self.num_windows), 1)
                self.done = [False] * num_of_files_to_create  # update status lists
                self.counter = [0] * num_of_files_to_create  # update status lists
                if num_of_files_to_create > 0:
                    for i in range(num_of_files_to_create):
                        f = open("namelist_split{num}.txt".format(num=i), "w")
                        split_namelists.append(f)
                    for idx, name in enumerate(difference):
                        split_namelists[idx % num_of_files_to_create].write(name)
                    for file in split_namelists:
                        file.close()


    def browser(self, userlist, index, channel):
        try:
            with open(userlist, "r") as _namelist, open("banned_part{index}.txt".format(index=index), "w+") as banned_names:
                if len(_namelist.readlines()) > 0:
                    _namelist.seek(0)
                    profile = webdriver.FirefoxProfile(self.config["Firefox_profile"])
                    profile.set_preference("security.insecure_field_warning.contextual.enabled", False)
                    profile.set_preference("security.enterprise_roots.enabled", True)
                    options = Options()
                    if index != 0 and self.headless_mode:
                        options.add_argument('--headless')
                    with webdriver.Firefox(options=options, executable_path="FirefoxPortable/App/Firefox64/geckodriver.exe", firefox_profile=profile,
                                           firefox_binary="FirefoxPortable/App/Firefox64/firefox.exe") as driver:
                        # print(driver.profile.profile_dir)
                        driver.set_window_size(1000, 1000)
                        wait = WebDriverWait(driver, 60)
                        wait_rules = WebDriverWait(driver, 10)
                        driver.get("https://www.twitch.tv/popout/{channel}/chat".format(channel=channel))
                        chat_field = wait.until(presence_of_element_located((By.CSS_SELECTOR, ".ScInputBase-sc-1wz0osy-0")))
                        chat_welcome_message = wait.until(presence_of_element_located((By.CSS_SELECTOR, ".chat-line__status")))
                        if chat_field.is_displayed():
                            chat_field.click()
                        try:  # remove rules window
                            rules_button = wait_rules.until(presence_of_element_located((By.CSS_SELECTOR, ".dhNyXR")))
                            if rules_button.is_displayed():
                                rules_button.click()
                        except (NoSuchElementException, TimeoutException):
                            pass
                        if chat_field.is_displayed():
                            chat_field.click()
                        for _name in _namelist:
                            try:
                                chat_field = wait.until(presence_of_element_located((By.CSS_SELECTOR, ".ScInputBase-sc-1wz0osy-0")))
                                chat_field.send_keys("{cmd} {name}".format(cmd=self.command, name=_name), Keys.ENTER)
                                banned_names.write(_name)
                                self.counter[index] += 1
                            except (ElementNotInteractableException, ElementClickInterceptedException):
                                pass
        except LookupError:
            print("couldn't start instance {}".format(index))
        finally:
            self.done[index] = True


    def start_browsers(self, channel):
        num_names = 0
        split_banlists = glob.glob("namelist_split*.txt")
        num_banlists = len(split_banlists)
        for filePath in split_banlists:
            with open(filePath, "r") as split_file:
                num_names += len(split_file.readlines())

        if num_names > 0:
            start = time.time()
            for idx, namelist in enumerate(split_banlists):
                _thread.start_new_thread(self.browser, (namelist, idx, channel))
                time.sleep(2)
            progressbar = tqdm(total=num_names, unit=" Names", file=sys.stdout, colour="#0FEED0")
            old_sum = 0
            new_sum = sum(self.counter)
            while sum(self.done) < num_banlists:
                old_sum = new_sum
                new_sum = sum(self.counter)
                progressbar.update(new_sum-old_sum)
                # print("Progress: {prog:.2%}  Elapsed time: {elapsed}".format(prog=sum(self.counter) / num_names,
                #                                                              elapsed=str(datetime.timedelta(seconds=int(time.time() - start)))))
                time.sleep(0.01)
            part_files = glob.glob("banned_part*.txt")
            with open("banned_lists/{streamer}.txt".format(streamer=channel), "a") as banlist:
                for filePath in part_files:
                    with open(filePath, "r") as part_file:
                        banlist.write(part_file.read())
                    os.remove(filePath)

    def run(self):
        self.load_config()
        self.check_files()
        for chnl in self.channels:
            self.split_files(chnl)
            self.start_browsers(chnl)
            self.delete_split_namelists()


if __name__ == "__main__":
    tool = Bantool()
    tool.run()
