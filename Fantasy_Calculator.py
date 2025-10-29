import pandas as pd
import sys
#import numpy as np
#import subprocess
#from collections import defaultdict
#from IPython.display import HTML, display
#import requests
#from bs4 import BeautifulSoup
#import ast
pd.set_option('display.max_columns', None)
from Imports import PYScripts as ps
from pprint import pprint


csv_filepath = 'CSVs/SuperFlex.csv'

try:
    df = pd.read_csv(csv_filepath)
except FileNotFoundError:
    print(f"Error: The file '{csv_filepath}' was not found.")
    sys.exit(1)
except Exception as e:
    print(f"Error reading CSV file: {e}")
    sys.exit(1)

#GC Score
GC_QB = 'Patrick Mahomes'
GC_WR1 = 'A.J. Brown'
GC_WR2 = 'Xavier Worthy'
GC_WR3 = 'Terry McLaurin'
GC_RB1 = 'Alvin Kamara'
GC_RB2 = 'Kimani Vidal'
GC_TE = 'Dalton Schultz'
GC_Flex = 'Rhamondre Stevenson'
GC_Bench1 = 'Sam LaPorta'
GC_Bench2 = 'Brian Thomas'
GC_Bench3 = 'Bucky Irving'
GC_Bench4 = 'Brian Robinson'
GC_Bench5 = 'Tez Johnson'
GC_IR = 'Trey Benson'
GC_DEF_approx = 7.5
GC_Team = [GC_QB, GC_WR1, GC_WR2, GC_WR3, GC_RB1, GC_RB2, GC_TE, GC_Flex]
GC_Score = 0
GC_DF = []
for player in GC_Team:
    if player in df['Player'].values:  
        GC_Score += df.loc[df['Player'] == player, 'PPR'].iloc[0]
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        GC_DF.append(row)
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
print(f"\n GC Score    = {round(GC_Score+GC_DEF_approx, 2)} \n")
pprint(GC_DF)


#Noche Score
Noche_QB1 = 'Bo Nix'
Noche_WR1 = "Ja'Marr Chase"
Noche_WR2 = 'Stefon Diggs'
Noche_WR3 = 'Justin Jefferson'
Noche_RB1 = 'Cam Skattebo'
Noche_RB2 = 'Alvin Kamara'
Noche_TE = 'Dallas Goedert'
Noche_Flex = 'Jordan Mason'
Noche_SuperFlex = 'Cade Otton'
Noche_Bench1 = 'Hunter Henry'
Noche_Bench2 = 'Jared Goff'
Noche_Bench3 = 'Kyren Williams'
Noche_Bench4 = 'Cooper Kupp'
Noche_DEF_approx = 14.33
Noche_Team = [Noche_QB1, Noche_WR1, Noche_WR2, Noche_WR3, Noche_RB1, Noche_RB2, Noche_TE, Noche_Flex, Noche_SuperFlex]
Noche_Score = 0
Noche_DF = []
for player in Noche_Team:
    if player in df['Player'].values:  
        Noche_Score += df.loc[df['Player'] == player, 'PPR'].iloc[0]
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        Noche_DF.append(row)    
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
print(f"\n Noche Score = {round(Noche_Score+Noche_DEF_approx, 2)} \n")
pprint(Noche_DF)


#Paint Score
Paint_QB = 'Michael Penix'
Paint_WR1 = 'Nico Collins'
Paint_WR2 = 'Rashid Shaheed'
Paint_WR3 = 'D.J. Moore'
Paint_RB1 = 'Jonathan Taylor'
Paint_RB2 = 'Breece Hall'
Paint_TE = 'Dallas Goedert'
Paint_Flex = 'Rachaad White'
Paint_Bench1 = 'Jared Goff'
Paint_Bench2 = 'Jaxon Smith-Njigba'
Paint_Bench3 = 'Puka Nacua'
Paint_Bench4 = 'Rico Dowdle'
Paint_Bench5 = 'Kimani Vidal'
Paint_IR = 'Trey Benson'
Paint_K_approx = 8.60
Paint_DEF_approx = 16.00
Paint_Team = [Paint_QB, Paint_WR1, Paint_WR2, Paint_WR3, Paint_RB1, Paint_RB2, Paint_TE, Paint_Flex]
Paint_Score = 0
Paint_DF = []
for player in Paint_Team:
    if player in df['Player'].values:  
        Paint_Score += df.loc[df['Player'] == player, 'STD'].iloc[0]
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        Paint_DF.append(row)    
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
print(f"\n Paint Score = {round(Paint_Score+Paint_K_approx+Paint_DEF_approx, 2)} \n")
pprint(Paint_DF)

#Jerks Score
Jerks_QB1 = 'Jaxson Dart'
Jerks_QB2 = 'Carson Wentz'
Jerks_WR1 = 'Stefon Diggs'
Jerks_WR2 = 'Quentin Johnston'
Jerks_WR3 = 'Alec Pierce'
Jerks_RB1 = 'Jordan Mason'
Jerks_RB2 = 'James Cook'
Jerks_TEFlex = 'Cade Otton'
Jerks_Flex1 = 'J.K. Dobbins'
Jerks_Flex2 = 'Xavier Worthy'
Jerks_Flex3 = 'Rachaad White'
Jerks_Flex4 = "D'Andre Swift"
Jerks_Flex5 = 'Calvin Ridley'
Jerks_Bench1 = 'Jayden Daniels'
Jerks_Bench2 = 'Jahmyr Gibbs'
Jerks_Bench3 = 'Marvin Harrison Jr.'
Jerks_IR = 'Brock Bowers'
Jerks_Team = [Jerks_QB1, Jerks_QB2, Jerks_WR1, Jerks_WR2, Jerks_WR3, Jerks_RB1, Jerks_RB2, Jerks_TEFlex, Jerks_Flex1, Jerks_Flex2, Jerks_Flex3, Jerks_Flex4, Jerks_Flex5]
Jerks_Score = 0
Jerks_DF = []
for player in Jerks_Team:
    if player in df['Player'].values:  
        Jerks_Score += df.loc[df['Player'] == player, 'PPR'].iloc[0]
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        Jerks_DF.append(row)    
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
print(f"\n Jerks Score = {round(Jerks_Score, 2)} \n")
pprint(Jerks_DF)





