import pandas as pd
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

hitting = ps.hitterpredictions('CSVs/MLB_Ind_Stats_2023.csv', 'CSVs/MLB_Ind_Stats_2024.csv', 'CSVs/MLB_Ind_Stats_2025.csv', 'CSVs/MLB_Spring_Stats_2026.csv')
pitching = ps.pitcherpredictions('CSVs/MLB_Pitch_Ind_2023.csv', 'CSVs/MLB_Pitch_Ind_2024.csv', 'CSVs/MLB_Pitch_Ind_2025.csv', 'CSVs/MLB_Pitch_Spring_2026.csv')
ps.preseasonmlbhittinghtml(hitting)
ps.preseasonmlbpitchinghtml(pitching)
print('completed')