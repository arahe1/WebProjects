import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PYScripts as ps

directory_path = "CSVs"

listicle = ['CSVs/Week_1_Scores_2025.csv',
            'CSVs/Week_2_Scores_2025.csv',
            'CSVs/Week_3_Scores_2025.csv',
            'CSVs/Week_4_Scores_2025.csv',
            'CSVs/Week_5_Scores_2025.csv',
            'CSVs/Week_6_Scores_2025.csv',
            'CSVs/Week_7_Scores_2025.csv',
            'CSVs/Week_8_Scores_2025.csv',
            'CSVs/Week_9_Scores_2025.csv',
            'CSVs/Week_10_Scores_2025.csv']

DFs = ps.weeklyteamwinner(listicle)
Week = len(DFs)+1
Schedule = ps.schedulemaker('CSVs/Schedule_2025.csv')
HomeField = ps.teamwinnerschedule('CSVs/Schedule_2025.csv', Week)
Useful = ps.teamuseful(DFs, Week, Schedule)
FinalScores = ps.teammc(Useful,HomeField)
ps.teampredictionshtml(FinalScores, Week)




commit_msg = f"Adding data and producing team predictions for Week {Week-1}"

try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Git auto-update complete.")
except subprocess.CalledProcessError:
    print("Git command failed (maybe no changes to commit?)")

