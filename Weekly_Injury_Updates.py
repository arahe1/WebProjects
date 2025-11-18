import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PYScripts as ps

directory_path = "CSVs"
Week = 0
for filename in os.listdir(directory_path):
    # Only count files (not directories)
    if os.path.isfile(os.path.join(directory_path, filename)) and "NFL" in filename:
        Week += 1


SuperFlex = pd.read_csv("CSVs/SuperFlex.csv")
SuperFlex = ps.injuryremovalweekly(SuperFlex)
All_DataFrames = ps.weeklyfinaldataframes(SuperFlex)
df = All_DataFrames['SuperFlex']



full_path = os.path.join('CSVs', 'SuperFlex.csv')
df.to_csv(full_path, index=False)

ps.weeklyhtml(All_DataFrames, Week)

commit_msg = f"Removing players either Out or on Injured Reserve for Week {Week-1}"

try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Git auto-update complete.")
except subprocess.CalledProcessError:
    print("Git command failed (maybe no changes to commit?)")


