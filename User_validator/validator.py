import sys

from twitchAPI.twitch import Twitch
import time
import tqdm


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# create instance of twitch API
twitch = Twitch(app_id='app_id', app_secret="app_secret")
twitch.authenticate_app([])

# get ID of users
with open("inputlist.txt", "r") as names:
    name_lines = names.readlines()

name_set = set()
for name_line in name_lines:
    name = name_line.strip().lower()
    name_set.add(name)
name_list = list(sorted(name_set))
output_set = set()

chunked_namelists = [*chunks(name_list, 100)]

progressbar = tqdm.tqdm(chunked_namelists, file=sys.stdout, ascii=True)

with open("namelist_cleaned.txt", "w") as output_file:
    for chunk in progressbar:
        # print("requesting")
        user_infos = twitch.get_users(logins=chunk).get("data")
        for user_info in user_infos:
            output_file.write(f"{user_info.get('login')}\n")
            output_file.flush()
            # print(user_info.get("login"))

with open("namelist_cleaned.txt", "r") as output_file:
    num_output = len(output_file.readlines())
    num_input = len(name_list)
    if num_input:
        print(f'Valid user ratio: {num_output/num_input:.2%}')
