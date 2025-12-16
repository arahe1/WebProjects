import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PYScripts as ps

from Imports import PYScripts as ps

listicle = ['CSVs/Week_1_NFL_2025.csv',
            'CSVs/Week_2_NFL_2025.csv',
            'CSVs/Week_3_NFL_2025.csv',
            'CSVs/Week_4_NFL_2025.csv',
            'CSVs/Week_5_NFL_2025.csv',
            'CSVs/Week_6_NFL_2025.csv',
            'CSVs/Week_7_NFL_2025.csv',
            'CSVs/Week_8_NFL_2025.csv',
            'CSVs/Week_9_NFL_2025.csv',
            'CSVs/Week_10_NFL_2025.csv',
            'CSVs/Week_11_NFL_2025.csv',
            'CSVs/Week_12_NFL_2025.csv',
            'CSVs/Week_13_NFL_2025.csv',
            'CSVs/Week_14_NFL_2025.csv',
            'CSVs/Week_15_NFL_2025.csv']

DFs = ps.importstats(listicle)
Schedule = ps.schedulemaker('CSVs/Schedule_2025.csv')
Week = len(DFs)+1
Total_Stats = ps.totalstatcombiner(DFs)
IndividualTotals = ps.individualtotals(DFs)
Useful = ps.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)
TeamTotals = ps.teamtotals(DFs, Schedule)
ROS = ps.ROSdataframe(Useful, TeamTotals, Week, Schedule)
All_DataFrames = ps.rosfinaldataframes(ROS)
All_DataFrames['Rest Of Season'] = ps.injuryremovalros(All_DataFrames['Rest Of Season'])
df = All_DataFrames['Rest Of Season']

full_path = os.path.join('CSVs', 'Rest_Of_Season.csv')
df.to_csv(full_path, index=False)

ps.roshtml(All_DataFrames)

commit_msg = f"Adding data for Week {Week-1} and Producing predictions for Rest Of Season"

try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Git auto-update complete.")
except subprocess.CalledProcessError:
    print("Git command failed (maybe no changes to commit?)")