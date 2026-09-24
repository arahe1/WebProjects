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
Useful = ps.usefulstats(DFs, Total_Stats, IndividualTotals)
schedule_df = ps.get_schedule(Schedule, Week)
Useful = Useful.merge(schedule_df,on='Team',how='left')
TeamTotals = ps.teamtotals(DFs2, Schedule)
TeamTotals_last = ps.teamtotals(DFs1, Schedule_last)

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
