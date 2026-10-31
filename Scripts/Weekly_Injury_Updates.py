import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

directory_path = "CSVs"
Week = 1
year = "2026"  

for filename in os.listdir(directory_path):
    # Only count files containing "NFL" and the specified year
    if (os.path.isfile(os.path.join(directory_path, filename))
            and "NFL" in filename
            and year in filename):
        Week += 1


SuperFlex = pd.read_csv("CSVs/SuperFlex.csv")
SuperFlex = ps.get_starting_qbs(SuperFlex)
SuperFlex = ps.injuryremovalweekly(SuperFlex)
All_DataFrames = ps.weeklyfinaldataframes(SuperFlex)
df = All_DataFrames['SuperFlex']



full_path = os.path.join('CSVs', 'SuperFlex.csv')
df.to_csv(full_path, index=False)

ps.weeklyhtml(All_DataFrames, Week)

print("Injuries Updated")



