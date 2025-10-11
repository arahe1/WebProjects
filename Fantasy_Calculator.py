import pandas as pd
import numpy as np
from collections import defaultdict
from IPython.display import HTML, display
import requests
from bs4 import BeautifulSoup
import ast
pd.set_option('display.max_columns', None)
from Imports import CSV_Importer as ci
from Imports import Schedule_Maker as sm
from Imports import Total_Stats_Combiner as tsc
from Imports import Create_Individual_Totals as cit
from Imports import Create_Useful as cu
from Imports import Create_Team_Totals as ctt
from Imports import Weekly_Final_Dataframes as wfd
from Imports import Create_Weekly_HTML as wrh
from Imports import Injury_Removal as ir

listicle = ['CSVs/Week_1_NFL_2025.csv','CSVs/Week_2_NFL_2025.csv','CSVs/Week_3_NFL_2025.csv','CSVs/Week_4_NFL_2025.csv','CSVs/Week_5_NFL_2025.csv']
DFs = ci.importstats(listicle)
Schedule = sm.schedulemaker('CSVs/Schedule_2025.csv')
Week = len(DFs)+1
Total_Stats = tsc.totalstatcombiner(DFs)
IndividualTotals = cit.individualtotals(DFs)
Useful = cu.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)
Useful = ir.injuryremoval(Useful)
TeamTotals = ctt.teamtotals(DFs, Schedule)
All_DataFrames = wfd.weeklyfinaldataframes(Useful, TeamTotals)


SuperFlex = All_DataFrames["SuperFlex"]
    
#GC Score
GC_Team = ['Patrick Mahomes', 'A.J. Brown', 'Brian Thomas', 'Xavier Worthy', 'Alvin Kamara', 'Rhamondre Stevenson', 'Sam LaPorta', 'Troy Franklin']
GC_Score = 0
Score = 0
for player in GC_Team:
    if player in SuperFlex['Player'].values:  
        Score = SuperFlex.loc[SuperFlex['Player'] == player, 'PPR'].iloc[0]
        GC_Score += Score
    else:
        print(f"{player} not found in the DataFrame.")

#Noche Score
Noche_Team = ['Bo Nix', "Ja'Marr Chase", 'Stefon Diggs', 'Cooper Kupp', 'Kyren Williams', 'Alvin Kamara', 'Dallas Goedert', 'Cam Skattebo', 'Jared Goff']
Noche_Score = 0
Score = 0
for player in Noche_Team:
    if player in SuperFlex['Player'].values:  
        Score = SuperFlex.loc[SuperFlex['Player'] == player, 'PPR'].iloc[0]
        Noche_Score += Score
    else:
        print(f"{player} not found in the DataFrame.")

#Paint Score
Paint_Team = ['Jared Goff', 'Puka Nacua', 'Jaxon Smith-Njigba', 'D.J. Moore', 'Jonathan Taylor', 'Breece Hall', 'Dallas Goedert', 'Rachaad White']
Paint_Score = 0
Score = 0
for player in Paint_Team:
    if player in SuperFlex['Player'].values:  
        Score = SuperFlex.loc[SuperFlex['Player'] == player, 'STD'].iloc[0]
        Paint_Score += Score
    else:
        print(f"{player} not found in the DataFrame.")

#Jerks Score
Jerks_Team = ['Jaxson Dart', 'Jayden Daniels', 'Calvin Ridley', 'Stefon Diggs', 'Marvin Harrison Jr.', 'James Cook', 'Jahmyr Gibbs', 'Quentin Johnston', 'Xavier Worthy', 'J.K. Dobbins', 'Michael Carter', 'Rachaad White', "D'Andre Swift"]
Jerks_Score = 0
Score = 0
for player in Jerks_Team:
    if player in SuperFlex['Player'].values:  
        Score = SuperFlex.loc[SuperFlex['Player'] == player, 'PPR'].iloc[0]
        Jerks_Score += Score
    else:
        print(f"{player} not found in the DataFrame.")






print('GC Score    =', GC_Score.round(2), 'Noche Score =', Noche_Score.round(2), 'Paint Score =', Paint_Score.round(2), 'Jerks Score =', Jerks_Score.round(2))