import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

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
            'CSVs/Week_15_NFL_2025.csv',
            'CSVs/Week_16_NFL_2025.csv']

DFs = ps.importstats(listicle)
Schedule = ps.schedulemaker('CSVs/Schedule_2025.csv')
Week = len(DFs)+1
Total_Stats = ps.totalstatcombiner(DFs)
IndividualTotals = ps.individualtotals(DFs)
Useful = ps.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)
TeamTotals = ps.teamtotals(DFs, Schedule)
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



