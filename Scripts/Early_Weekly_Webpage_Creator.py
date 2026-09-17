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

Week = len(DFs2)+1

Total_Stats1 = ps.totalstatcombiner(DFs1)
Total_Stats2 = ps.totalstatcombiner(DFs2)


IndividualTotals1 = ps.individualtotals(DFs1)
IndividualTotals2 = ps.individualtotals(DFs2)

Useful = ps.usefulstats(DFs1, Week, Schedule, Total_Stats1, IndividualTotals1)

TeamTotals = ps.teamtotals(DFs2, Schedule)
print(Useful.head())
SuperFlex = ps.weeklySuperFlexdataframe(Useful, TeamTotals)

SuperFlex = ps.injuryremovalweekly(SuperFlex)
All_DataFrames = ps.weeklyfinaldataframes(SuperFlex)
df = All_DataFrames['SuperFlex']

full_path = os.path.join('CSVs', 'Useful.csv')
Useful.to_csv(full_path, index=False)

full_path = os.path.join('CSVs', 'SuperFlex.csv')
df.to_csv(full_path, index=False)

ps.weeklyhtml(All_DataFrames, Week)

print("Predictions Updated")
