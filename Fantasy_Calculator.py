import pandas as pd
import numpy as np
import subprocess
from collections import defaultdict
from IPython.display import HTML, display
pd.set_option('display.max_columns', None)
from Imports import CSV_Importer as ci
from Imports import Schedule_Maker as sm
from Imports import Total_Stats_Combiner as tsc
from Imports import Create_Individual_Totals as cit
from Imports import Create_Useful as cu
from Imports import Create_Team_Totals as ctt
from Imports import ROS_Final_Dataframes as rfd

listicle = ['CSVs/Week_1_NFL_2025.csv','CSVs/Week_2_NFL_2025.csv','CSVs/Week_3_NFL_2025.csv','CSVs/Week_4_NFL_2025.csv','CSVs/Week_5_NFL_2025.csv']
DFs = ci.importstats(listicle)
Schedule = sm.schedulemaker('CSVs/Schedule_2025.csv')
Week = len(DFs)+1
Total_Stats = tsc.totalstatcombiner(DFs)
IndividualTotals = cit.individualtotals(DFs)
Useful = cu.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)
TeamTotals = ctt.teamtotals(DFs, Schedule)
All_DataFrames = rfd.rosfinaldataframes(Useful, TeamTotals, Week, Schedule)


def fantasycalc(superflex):
    
    #GC Score
    GC_Team = ['Patrick Mahomes', 'A.J. Brown', 'Brian Thomas', 'Xavier Worthy', 'Bucky Irving', 'Rhamondre Stevenson', 'Sam LaPorta', 'Terry McLaurin']
    GC_Score = 0
    Score = 0
    for player in GC_Team:
        if player in superflex['Player'].values:  
            Score = superflex.loc[superflex['Player'] == player, 'PPR'].iloc[0]
            GC_Score += Score
        else:
            print(f"{player} not found in the DataFrame.")

    #Noche Score
    Noche_Team = ['Bo Nix', "Ja'Marr Chase", 'Stefon Diggs', 'Nick Westbrook-Ikhine', 'Kyren Williams', 'Alvin Kamara', 'Hunter Henry', 'Cam Skattebo', 'Jared Goff']
    Noche_Score = 0
    Score = 0
    for player in Noche_Team:
        if player in superflex['Player'].values:  
            Score = superflex.loc[superflex['Player'] == player, 'PPR'].iloc[0]
            Noche_Score += Score
        else:
            print(f"{player} not found in the DataFrame.")

    #Paint Score
    Paint_Team = ['Jared Goff', 'Puka Nacua', 'Jaxon Smith-Njigba', 'D.J. Moore', 'Jonathan Taylor', 'Breec Hall', 'Dallas Goedert', 'Rachaad White']
    Paint_Score = 0
    Score = 0
    for player in GC_Team:
        if player in superflex['Player'].values:  
            Score = superflex.loc[superflex['Player'] == player, 'STD'].iloc[0]
            Paint_Score += Score
        else:
            print(f"{player} not found in the DataFrame.")

    #Jerks Score
    Jerks_Team = ['Jaxson Dart', 'Jayden Daniels', 'Calvin Ridley', 'Stefon Diggs', 'Marvin Harrison Jr.', 'James Cook III', 'Jahmyr Gibbs', 'Quentin Johnston', 'Xavier Worthy', 'J.K. Dobbins', 'Chris Godwin Jr.', 'Rachaad White', "D'Andre Swift"]
    Jerks_Score = 0
    Score = 0
    for player in GC_Team:
        if player in superflex['Player'].values:  
            Score = superflex.loc[superflex['Player'] == player, 'PPR'].iloc[0]
            Jerks_Score += Score
        else:
            print(f"{player} not found in the DataFrame.")






    return ('GC Score    =', GC_Score.round(2)), ('Noche Score =', Noche_Score.round(2)), ('Paint Score =', Paint_Score.round(2)), ('Jerks Score =', Jerks_Score.round(2))