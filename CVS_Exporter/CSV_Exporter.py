import csv
import os

follow_dict = dict()
if not os.path.isfile("Followerlist.csv"):
    with open("Followerlist.csv", "x"):
        pass
if not os.path.isfile("Bots.txt"):
    with open("Bots.txt", "x"):
        pass

with open("Followerlist.csv", "r", newline='') as input_file:
    input_csv = csv.reader(input_file)
    for line in input_csv:
        if line:
            if line != ['userName', 'userID', 'accCreatedAt', 'followCreatedAt'] or line != ['userName', 'userID', 'accCreatedAt', 'followCreatedAt', 'isKnownBot']:
                username, userID, create_time, follow_time = line
                if follow_time in follow_dict.keys():
                    follow_dict[follow_time].append((username, userID))
                else:
                    follow_dict[follow_time] = [(username, userID)]

with open("Bots.txt", "w") as name_file, open("Bots_IDs.txt", "w") as id_file:
    for time, name_and_ID_list in follow_dict.items():
        if len(name_and_ID_list) > 10:
            for name_id in name_and_ID_list:
                name_file.write(name_id[0] + "\n")
                id_file.write(name_id[1] + "\n")
