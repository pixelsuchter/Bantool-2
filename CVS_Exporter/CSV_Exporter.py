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
            if line != ['userName', 'userID', 'accCreatedAt', 'followCreatedAt'] and line != ['userName', 'userID', 'accCreatedAt', 'followCreatedAt', 'isKnownBot']:
                isBot = 0
                if len(line) == 4:
                    username, userID, create_time, follow_time = line
                else:
                    username, userID, create_time, follow_time, isBot = line
                if follow_time in follow_dict.keys():
                    follow_dict[follow_time].append((username, userID, isBot))
                else:
                    follow_dict[follow_time] = [(username, userID, isBot)]

with open("Bots.txt", "w") as name_file, open("Bots_IDs.txt", "w") as id_file:
    for time, name_and_ID_list in follow_dict.items():
        if len(name_and_ID_list) > 10:
            for name_id in name_and_ID_list:
                name_file.write(name_id[0] + "\n")
                id_file.write(name_id[1] + "\n")
        else:
            for name_id in name_and_ID_list:
                if name_id[2] == "1":
                    name_file.write(name_id[0] + "\n")
                    id_file.write(name_id[1] + "\n")
