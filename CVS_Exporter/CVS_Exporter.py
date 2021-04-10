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
        if line != ['userName', 'userID', 'accCreatedAt', 'followCreatedAt']:
            username, userID, create_time, follow_time = line
            if follow_time in follow_dict.keys():
                follow_dict[follow_time].append(username)
            else:
                follow_dict[follow_time] = [username]

with open("Bots.txt", "w") as output_file:
    for time, namelist in follow_dict.items():
        if len(namelist) > 10:
            for name in namelist:
                output_file.write(name + "\n")
