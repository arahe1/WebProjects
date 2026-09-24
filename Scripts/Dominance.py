import pandas as pd
import os
import subprocess
import matplotlib.pyplot as plt
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

listicle = ps.get_nfl_week_files(2026, folder="CSVs")
DFs = ps.importstats(listicle)
DFs = [df.replace("WAS", "WSH") for df in DFs]
Schedule = ps.schedulemaker('CSVs/Schedule_2026.csv')
Week = len(DFs)+1
Total_Stats = ps.totalstatcombiner(DFs)
IndividualTotals = ps.individualtotals(DFs)
Useful = ps.usefulstats(DFs, Total_Stats, IndividualTotals)
TeamTotals = ps.teamtotals(DFs, Schedule)
print(TeamTotals)
OffenseTotals = ps.calculate_offense(TeamTotals)
schedule_df = ps.get_schedule(Schedule, Week)
Useful = Useful.merge(schedule_df,on='Team',how='left')
Dominance = ps.analysis(Useful,IndividualTotals)

for name, dataframe in Dominance.items():
    dataframe = dataframe.merge(OffenseTotals[['Team', 'OffYds+', 'OffTD+']], on='Team', how='left')
    dataframe['Off Focus'] = pd.to_numeric(dataframe['Off Focus'], errors='coerce')
    dataframe['OffYds+'] = pd.to_numeric(dataframe['OffYds+'], errors='coerce')
    dataframe['OffTD+'] = pd.to_numeric(dataframe['OffTD+'], errors='coerce')
    dataframe['Dominance'] = (dataframe['Off Focus'] + dataframe['OffYds+']).round(2)
    columns = list(dataframe.columns)
    columns.insert(3, columns.pop(columns.index('Dominance')))
    columns.insert(4, columns.pop(columns.index('Off Focus')))
    columns.insert(5, columns.pop(columns.index('OffYds+')))
    columns.insert(6, columns.pop(columns.index('OffTD+')))
    dataframe = dataframe[columns]
    Dominance[name] = dataframe

ps.dominancehtml(Dominance)

print("Dominance Updated")


# for name, df in Dominance.items():
#     if name == 'QB':
#         df = df[df['Dominance'] > 2]
#         plt.hist(df['Dominance'], bins=10, color='blue', edgecolor='black')
#         plt.title(f'Histogram of {name}')
#         plt.xlabel('Score')
#         plt.ylabel('Frequency')
#         plt.show()
#     if name == 'WR':
#         df = df[df['Dominance'] > 40]
#         plt.hist(df['Dominance'], bins=20, color='green', edgecolor='black')
#         plt.title(f'Histogram of {name}')
#         plt.xlabel('Score')
#         plt.ylabel('Frequency')
#         plt.show()
#     if name == 'RB':
#         df = df[df['Dominance'] > 40]
#         plt.hist(df['Dominance'], bins=20, color='orange', edgecolor='black')
#         plt.title(f'Histogram of {name}')
#         plt.xlabel('Score')
#         plt.ylabel('Frequency')
#         plt.show()
#     if name == 'TE':
#         df = df[df['Dominance'] > 40]
#         plt.hist(df['Dominance'], bins=20, color='red', edgecolor='black')
#         plt.title(f'Histogram of {name}')
#         plt.xlabel('Score')
#         plt.ylabel('Frequency')
#         plt.show()
    



