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
GC_Team = ['Patrick Mahomes', 'A.J. Brown', 'Terry McLaurin', 'Xavier Worthy', 'Alvin Kamara', 'Rhamondre Stevenson', 'Dalton Schultz', 'Kimani Vidal']
GC_Score = 0

for player in GC_Team:
    if player in df['Player'].values:  
        GC_Score = df.loc[df['Player'] == player, 'PPR'].iloc[0]
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()

#Noche Score
Noche_Team = ['Bo Nix', "Ja'Marr Chase", 'Stefon Diggs', 'Justin Jefferson', 'Cam Skattebo', 'Alvin Kamara', 'Dallas Goedert', 'Jordan Mason', 'Cade Otton']
Noche_Score = 0
for player in Noche_Team:
    if player in df['Player'].values:  
        Noche_Score = df.loc[df['Player'] == player, 'PPR'].iloc[0]
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()

#Paint Score
Paint_Team = ['Michael Penix', 'Nico Collins', 'Rashid Shaheed', 'D.J. Moore', 'Jonathan Taylor', 'Breece Hall', 'Dallas Goedert', 'Rachaad White']
Paint_Score = 0
for player in Paint_Team:
    if player in df['Player'].values:  
        Paint_Score = df.loc[df['Player'] == player, 'STD'].iloc[0]
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()

#Jerks Score
Jerks_Team = ['Jaxson Dart', 'Carson Wentz', 'Stefon Diggs', 'Quentin Johnston', 'Alec Pierce', 'Jordan Mason', 'James Cook', 'Cade Otton', 'J.K. Dobbins', 'Xavier Worthy', 'Rachaad White', "D'Andre Swift", 'Calvin Ridley']
Jerks_Score = 0
for player in Jerks_Team:
    if player in df['Player'].values:  
        Jerks_Score = df.loc[df['Player'] == player, 'PPR'].iloc[0]
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()






print(f"GC Score    = {round(GC_Score, 2)}\n Noche Score = {round(Noche_Score, 2)}\n Paint Score = {round(Paint_Score, 2)}\n Jerks Score = {round(Jerks_Score, 2)}")


