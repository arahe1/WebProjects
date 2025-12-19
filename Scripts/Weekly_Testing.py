import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps
import matplotlib.pyplot as plt

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
#print(Total_Stats[Total_Stats['Player'] == 'Jakobi Meyers'])
#print(len(Total_Stats['Player']))
IndividualTotals = ps.individualtotals(DFs)
#print(len(IndividualTotals['Player']))
Useful = ps.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)
#print(IndividualTotals.head())
#print(Useful.head())
Dominance = ps.analysis(Useful,IndividualTotals)



#combined = pd.concat([Dominance['WRDom'], Dominance['TEDom']], ignore_index=True)
combined = Dominance['WRDom']

points_sum = combined.groupby('Team', as_index=False)['Off Focus'].sum()
#points_sum = combined['Off Focus'].sum()
points_sum['Pass Focus'] = points_sum['Off Focus']
dominance_df = Dominance['RBDom'].groupby('Team', as_index=False)['Off Focus'].sum()
dominance_df['Run Focus'] = dominance_df['Off Focus']
merged = pd.merge(points_sum, dominance_df, on='Team')

merged[['Pass Focus', 'Run Focus']] = merged[['Pass Focus', 'Run Focus']] / merged[['Pass Focus', 'Run Focus']].max() * 100

avg_x = sum(merged['Pass Focus']) / len(merged['Pass Focus'])
avg_y = sum(merged['Run Focus']) / len(merged['Run Focus'])


plt.scatter(merged['Pass Focus'], merged['Run Focus'])

for i, row in merged.iterrows():
    plt.text(row['Pass Focus'], row['Run Focus'], row['Team'],
             fontsize=9, ha='right', va='bottom')  # adjust text position

plt.axvline(avg_x, color='black', linestyle='--', label=f'Avg X = {avg_x:.1f}')
plt.axhline(avg_y, color='black', linestyle='--', label=f'Avg Y = {avg_y:.1f}')

plt.xlabel('Pass Focus')
plt.ylabel('Run Focus')
plt.title('Offensive Focus')
plt.show()
#TeamTotals = ps.teamtotals(DFs, Schedule)
#SuperFlex = ps.weeklySuperFlexdataframe(Useful, TeamTotals)
#SuperFlex = ps.injuryremovalweekly(SuperFlex)
#All_DataFrames = ps.weeklyfinaldataframes(SuperFlex)
#df = All_DataFrames['SuperFlex']


