import pandas as pd
import numpy as np
import subprocess
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
GC_Total = []
Noche_Total = []
Paint_Total = []
Jerks_Total = []
n = 0
while n < 1000:

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
    GC_Total.append(GC_Score)

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
    Noche_Total.append(Noche_Score)

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
    Paint_Total.append(Paint_Score)

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
    Jerks_Total.append(Jerks_Score)

    n = n+1





print(f"GC Score    = {round(sum(GC_Total)/len(GC_Total), 2)}\n Noche Score = {round(sum(Noche_Total)/len(Noche_Total), 2)}\n Paint Score = {round(sum(Paint_Total)/len(Paint_Total), 2)}\n Jerks Score = {round(sum(Jerks_Total)/len(Jerks_Total), 2)}")


