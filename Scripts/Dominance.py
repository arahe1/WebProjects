import pandas as pd
import os
import subprocess
import matplotlib.pyplot as plt
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
Dominance = ps.analysis(Useful,IndividualTotals)

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
    



