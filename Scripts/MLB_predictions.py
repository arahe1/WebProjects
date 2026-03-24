import pandas as pd
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

preseason = ps.seasonpredictions('CSVs/MLB_Ind_Stats_2023.csv', 'CSVs/MLB_Ind_Stats_2024.csv', 'CSVs/MLB_Ind_Stats_2025.csv', 'CSVs/MLB_Spring_Stats_2026.csv')
ps.preseasonmlbhtml(preseason)
print('completed')