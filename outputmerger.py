import json
from os import listdir

complete = {"leagues": {}, "players": {}}
filenames = listdir("tmp_output")

for filename in filenames:
    with open("tmp_output/" + filename, "r") as f:
        info = json.load(f)
        complete["leagues"].update(info["leagues"])
        complete["players"].update(info["players"])

print("Leagues: {}\nPlayers: {}".format(len(complete["leagues"]), len(complete["players"])))

with open("merged_output.json", "w") as fop:
    json.dump(complete, fop, indent=4, sort_keys=True)
