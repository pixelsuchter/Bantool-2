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
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
    from selenium.webdriver.support.expected_conditions import presence_of_element_located

channels = [""]
command = None
num_windows = 0

try:
    with open("config.json", "r") as cfg:
        config = json.load(cfg)
        assert type(config["twitch_channels"]) == list
        assert type(config["command"]) == str
        assert type(config["Number_of_browser_windows"]) == int
        assert type(config["Firefox_profile"]) == str
    channels = config["twitch_channels"]
    command = config["command"]
    num_windows = config["Number_of_browser_windows"]
except (OSError, json.JSONDecodeError, AssertionError, KeyError) as e:
    print("Config file does not exist or corrupt, creating default config\n")
    if os.path.isfile("config.json"):
        if os.path.isfile("config.json.broken"):
            os.remove("config.json.broken")
        os.rename("config.json", "config.json.broken")
    with open("config.json", "w") as f:
        config = {"twitch_channels": [""], "command": "/ban", "Number_of_browser_windows": 1, "Firefox_profile": ""}
        json.dump(config, f)


def check_files():
    if not os.path.isfile("namelist.txt"):
        print("Namelist does not exist, creating file. Please insert names and restart")
        with open("namelist.txt", "x"):
            pass
        input("Press enter to exit")
        exit(0)

    if channels == [""] or not command or not num_windows or not config["Firefox_profile"]:
        print("Config not set correctly")
        input("Press enter to exit")
        exit(0)


def delete_split_namelists():
    namelist_files = glob.glob("namelist_split*.txt")
    for filePath in namelist_files:
        try:
            os.remove(filePath)
        except OSError:
            print("Error while deleting file : ", filePath)


def split_files(channel):
    split_namelists = []
    with open("namelist.txt", "r") as namelist:
        name_count = len(namelist.readlines())
        namelist.seek(0)
        if not os.path.isdir("banned_lists"):  # create folder if nescessary
            os.mkdir("banned_lists")
        if not os.path.isfile("banned_lists/{streamer}.txt".format(streamer=channel)):  # create streamer specific file if non existant
            with open("banned_lists/{streamer}.txt".format(streamer=channel), "x"):
                pass
        delete_split_namelists()
        for i in range(num_windows):
            f = open("namelist_split{num}.txt".format(num=i), "w")
            split_namelists.append(f)
        with open("banned_lists/{streamer}.txt".format(streamer=channel), "r") as banned_names:
            _nameset = set(sorted(namelist.readlines()))
            _banned_set = set(sorted(banned_names.readlines()))
            print("Creating difference for {streamer}".format(streamer=channel))
            start = time.time()
            difference = _nameset.difference(_banned_set)
            end = time.time()
            print("Creating difference took {:.4f}s".format(end - start))
            for idx, name in enumerate(difference):
                split_namelists[idx % num_windows].write(name)
            for file in split_namelists:
                file.close()


def browser(userlist, index, channel):
    global counter, done
    try:
        with open(userlist, "r") as _namelist, open("banned_part{index}.txt".format(index=index), "w+") as banned_names:
            if len(_namelist.readlines()) > 0:
                _namelist.seek(0)
                profile = webdriver.FirefoxProfile(config["Firefox_profile"])
                profile.set_preference("security.insecure_field_warning.contextual.enabled", False)
                profile.set_preference("security.enterprise_roots.enabled", True)
                options = Options()
                if index != 0:
                    options.add_argument('--headless')
                with webdriver.Firefox(options=options, executable_path="FirefoxPortable/App/Firefox64/geckodriver.exe", firefox_profile=profile,
                                       firefox_binary="FirefoxPortable/App/Firefox64/firefox.exe") as driver:
                    print(driver.profile.profile_dir)
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
                            chat_field.send_keys("{cmd} {name}".format(cmd=command, name=_name), Keys.ENTER)
                            banned_names.write(_name)
                            counter[index] += 1
                        except (ElementNotInteractableException, ElementClickInterceptedException):
                            pass
    except LookupError:
        print("couldn't start instance {}".format(index))
    finally:
        done[index] = True


def start_browsers(channel):
    num_names = 0
    split_banlists = glob.glob("namelist_split*.txt")
    for filePath in split_banlists:
        with open(filePath, "r") as split_file:
            num_names += len(split_file.readlines())

    if num_names > 0:
        start = time.time()
        for i in range(num_windows):
            _thread.start_new_thread(browser, ("namelist_split{num}.txt".format(num=i), i, channel))
            time.sleep(2)
        while sum(done) < num_windows:
            print("Progress: {prog:.2%}  Elapsed time: {elapsed}".format(prog=sum(counter) / num_names,
                                                                         elapsed=str(datetime.timedelta(seconds=int(time.time() - start)))))
            time.sleep(1)
        part_files = glob.glob("banned_part*.txt")
        with open("banned_lists/{streamer}.txt".format(streamer=channel), "a") as banlist:
            for filePath in part_files:
                with open(filePath, "r") as part_file:
                    banlist.write(part_file.read())
                os.remove(filePath)


check_files()
for chnl in channels:
    counter = [0] * num_windows
    done = [False] * num_windows
    split_files(chnl)
    start_browsers(chnl)
    delete_split_namelists()
