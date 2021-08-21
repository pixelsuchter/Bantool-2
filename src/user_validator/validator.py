import sys
import json

import tqdm
from twitchAPI.twitch import Twitch


def main():
    with open("credentials.json", "r") as credential_file:
        credentials = json.load(credential_file)

    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    # create instance of twitch API
    twitch = Twitch(
        app_id=credentials["client id"], app_secret=credentials["app secret"]
    )
    twitch.authenticate_app([])

    with open("inputlist_user_ids.txt", "r") as ids:
        user_id_lines = ids.readlines()

    with open("inputlist_names.txt", "r") as names:
        name_lines = names.readlines()

    name_set = set()
    for name_line in name_lines:
        name = name_line.strip().lower()
        name_set.add(name)
    name_list = list(sorted(name_set))

    user_id_set = set()
    for user_id_line in user_id_lines:
        user_id = user_id_line.strip()
        user_id_set.add(user_id)
    user_id_list = list(sorted(user_id_set))

    chunked_namelists = [*chunks(name_list, 100)]
    chunked_user_id_lists = [*chunks(user_id_list, 100)]

    with open("namelist_cleaned.txt", "w") as name_file, open(
        "user_id_list_cleaned.txt", "w"
    ) as id_file:
        progressbar = tqdm.tqdm(
            chunked_namelists, file=sys.stdout, ascii=True, desc="User names"
        )
        for chunk in progressbar:
            user_infos = twitch.get_users(logins=chunk).get("data")
            for user_info in user_infos:
                name_file.write(f"{user_info.get('login')}\n")
                id_file.write(f"{user_info.get('id')}\n")
                name_file.flush()
                id_file.flush()

        progressbar = tqdm.tqdm(
            chunked_user_id_lists, file=sys.stdout, ascii=True, desc="User id's"
        )
        for chunk in progressbar:
            user_infos = twitch.get_users(user_ids=chunk).get("data")
            for user_info in user_infos:
                name_file.write(f"{user_info.get('login')}\n")
                id_file.write(f"{user_info.get('id')}\n")
                name_file.flush()
                id_file.flush()

    with open("namelist_cleaned.txt", "r") as output_file:
        num_output = len(output_file.readlines())
        num_input = len(name_list)
        if num_input:
            print(f'Valid user ratio: {num_output/num_input:.2%}')


if __name__ == "__main__":
    main()
