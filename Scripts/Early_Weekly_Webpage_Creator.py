import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

listicle1 = ps.get_nfl_week_files(2025, folder="CSVs")
listicle2 = ps.get_nfl_week_files(2026, folder="CSVs")

DFs1 = ps.importstats(listicle1)
DFs2 = ps.importstats(listicle2)
Schedule = ps.schedulemaker('CSVs/Schedule_2026.csv')
Schedule_last = ps.schedulemaker('CSVs/Schedule_2025.csv')
Week = len(DFs2)+1
Total_Stats = ps.totalstatcombiner(DFs1)
Total_Stats2 = ps.totalstatcombiner(DFs2)
IndividualTotals = ps.individualtotals(DFs2)
Useful = ps.usefulstats(DFs2, Week, Schedule, Total_Stats2, IndividualTotals)
TeamTotals = ps.teamtotals(DFs2, Schedule)
print(TeamTotals.tail(5))
TeamTotals_last = ps.teamtotals(DFs1, Schedule_last)
# 1. Find all columns that contain 'AAV' in df1
aav_cols = [col for col in TeamTotals.columns if 'AAV' in col]

# 2. Update df1 in place using the matching columns from df2
TeamTotals.update(TeamTotals_last[aav_cols])
print(TeamTotals.tail(5))

SuperFlex = ps.weeklySuperFlexdataframe(Useful, TeamTotals_last)
SuperFlex = ps.injuryremovalweekly(SuperFlex)
All_DataFrames = ps.weeklyfinaldataframes(SuperFlex)
df = All_DataFrames['SuperFlex']

full_path = os.path.join('CSVs', 'Useful.csv')
Useful.to_csv(full_path, index=False)

full_path = os.path.join('CSVs', 'SuperFlex.csv')
df.to_csv(full_path, index=False)

ps.weeklyhtml(All_DataFrames, Week)

print("Predictions Updated")
