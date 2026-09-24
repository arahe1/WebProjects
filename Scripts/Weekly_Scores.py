import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

directory_path = "CSVs"

listicle = ps.get_nfl_scores_files(2026, folder="CSVs")
DFs = ps.weeklyteamwinner(listicle)
Week = len(DFs)+1
Week = min(Week, 18)
Schedule = ps.schedulemaker('CSVs/Schedule_2026.csv')
Schedule = Schedule.replace("WSH", "WAS")
HomeField = ps.teamwinnerschedule('CSVs/Schedule_2026.csv', Week)
Useful = ps.teamuseful(DFs, Week, Schedule)
FinalScores = ps.teammc(Useful,HomeField)
print(FinalScores)
ps.teampredictionshtml(FinalScores, Week)




print("Scores Updated")


