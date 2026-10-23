import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

listicle = ps.get_nfl_week_files(2026, folder="CSVs")
DFs = ps.importstats(listicle)
Schedule = ps.schedulemaker('CSVs/Schedule_2026.csv')
Week = len(DFs)+1
Total_Stats = ps.totalstatcombiner(DFs)
IndividualTotals = ps.individualtotals(DFs)
Useful = ps.usefulstats(DFs, Total_Stats, IndividualTotals)
schedule_df = ps.get_schedule(Schedule, Week)
Useful = Useful.merge(schedule_df,on='Team',how='left')
TeamTotals = ps.teamtotals(DFs, Schedule)
TeamTotals = ps.apply_corrections(TeamTotals, DFs)
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



