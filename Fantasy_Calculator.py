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
GC_WR1 = 'Brian Thomas'
GC_WR2 = 'Xavier Worthy'
GC_WR3 = 'Terry McLaurin'
GC_RB1 = 'Alvin Kamara'
GC_RB2 = 'Kimani Vidal'
GC_TE = 'Sam LaPorta'
GC_Flex = 'Rhamondre Stevenson'
GC_Bench1 = 'Dalton Schultz'
GC_Bench2 = 'AJ Brown'
GC_Bench3 = 'Bucky Irving'
GC_Bench4 = 'Brian Robinson'
GC_Bench5 = 'Elic Ayomanor'
GC_IR = 'Trey Benson'
GC_DEF_approx = 9.43
GC_Team = [GC_QB, GC_WR1, GC_WR2, GC_WR3, GC_RB1, GC_RB2, GC_TE, GC_Flex]
GC_Bench = [GC_Bench1, GC_Bench2, GC_Bench3, GC_Bench4, GC_Bench5, GC_IR]
GC_Score = 0
GC_ScoreDF = []
GC_BenchDF = []
for player in GC_Team:
    if player in df['Player'].values:  
        GC_Score += df.loc[df['Player'] == player, 'PPR'].iloc[0]
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        GC_ScoreDF.append(row)
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
for player in GC_Bench:
    if player in df['Player'].values:  
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        GC_BenchDF.append(row)
    elif player == '':
        row = {'Player': player, 'Points': 0}
        GC_BenchDF.append(row) 
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
print(f"\n GC Score    = {round(GC_Score+GC_DEF_approx, 2)} \n")
pprint(GC_ScoreDF)
pprint(GC_BenchDF)


#Noche Score
Noche_QB1 = 'Bo Nix'
Noche_WR1 = "Ja'Marr Chase"
Noche_WR2 = 'Stefon Diggs'
Noche_WR3 = 'Justin Jefferson'
Noche_RB1 = 'Kyren Williams'
Noche_RB2 = 'Alvin Kamara'
Noche_TE = 'Hunter Henry'
Noche_Flex = 'Zonovan Knight'
Noche_SuperFlex = 'Jared Goff'
Noche_Bench1 = 'Dallas Goedert'
Noche_Bench2 = 'Kareem Hunt'
Noche_Bench3 = 'Jordan Mason'
Noche_Bench4 = 'Cooper Kupp'
Noche_IR = ''
Noche_DEF_approx = 14.33
Noche_Team = [Noche_QB1, Noche_WR1, Noche_WR2, Noche_WR3, Noche_RB1, Noche_RB2, Noche_TE, Noche_Flex, Noche_SuperFlex]
Noche_Bench = [Noche_Bench1, Noche_Bench2, Noche_Bench3, Noche_Bench4, Noche_IR]
Noche_Score = 0
Noche_ScoreDF = []
Noche_BenchDF = []
for player in Noche_Team:
    if player in df['Player'].values:  
        Noche_Score += df.loc[df['Player'] == player, 'PPR'].iloc[0]
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        Noche_ScoreDF.append(row)    
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
for player in Noche_Bench:
    if player in df['Player'].values:  
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        Noche_BenchDF.append(row)   
    elif player == '':
        row = {'Player': player, 'Points': 0}
        Noche_BenchDF.append(row) 
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
print(f"\n Noche Score = {round(Noche_Score+Noche_DEF_approx, 2)} \n")
pprint(Noche_ScoreDF)
pprint(Noche_BenchDF)


#Paint Score
Paint_QB = 'Jared Goff'
Paint_WR1 = 'Nico Collins'
Paint_WR2 = 'Jaxon Smith-Njigba'
Paint_WR3 = 'Puka Nacua'
Paint_RB1 = 'Jonathan Taylor'
Paint_RB2 = 'Kimani Vidal'
Paint_TE = 'Oronde Gadsden'
Paint_Flex = 'Zonovan Knight'
Paint_Bench1 = 'Rashid Shaheed'
Paint_Bench2 = 'Breece Hall'
Paint_Bench3 = 'Dallas Goedert'
Paint_Bench4 = 'Rico Dowdle'
Paint_Bench5 = 'Rachaad White'
Paint_IR = 'Trey Benson'
Paint_K_approx = 8.60
Paint_DEF_approx = 16.00
Paint_Team = [Paint_QB, Paint_WR1, Paint_WR2, Paint_WR3, Paint_RB1, Paint_RB2, Paint_TE, Paint_Flex]
Paint_Bench = [Paint_Bench1, Paint_Bench2, Paint_Bench3, Paint_Bench4, Paint_Bench5, Paint_IR]
Paint_Score = 0
Paint_ScoreDF = []
Paint_BenchDF = []
for player in Paint_Team:
    if player in df['Player'].values:  
        Paint_Score += df.loc[df['Player'] == player, 'STD'].iloc[0]
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        Paint_ScoreDF.append(row)    
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
for player in Paint_Bench:
    if player in df['Player'].values:  
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        Paint_BenchDF.append(row)   
    elif player == '':
        row = {'Player': player, 'Points': 0}
        Paint_BenchDF.append(row) 
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
print(f"\n Paint Score = {round(Paint_Score+Paint_K_approx+Paint_DEF_approx, 2)} \n")
pprint(Paint_ScoreDF)
pprint(Paint_BenchDF)


#Jerks Score
Jerks_QB1 = 'Jaxson Dart'
Jerks_QB2 = 'Jayden Daniels'
Jerks_WR1 = 'Stefon Diggs'
Jerks_WR2 = 'Quentin Johnston'
Jerks_WR3 = 'Marvin Harrison Jr.'
Jerks_RB1 = 'Jahmyr Gibbs'
Jerks_RB2 = 'James Cook'
Jerks_TEFlex = 'Brock Bowers'
Jerks_Flex1 = 'J.K. Dobbins'
Jerks_Flex2 = 'Xavier Worthy'
Jerks_Flex3 = "D'Andre Swift"
Jerks_Flex4 = 'Alec Pierce'
Jerks_Flex5 = 'Tyrone Tracy Jr.'
Jerks_Bench1 = 'Zonovan Knight'
Jerks_Bench2 = 'Cade Otton'
Jerks_Bench3 = 'Rachaad White'
Jerks_IR = ''
Jerks_Team = [Jerks_QB1, Jerks_QB2, Jerks_WR1, Jerks_WR2, Jerks_WR3, Jerks_RB1, Jerks_RB2, Jerks_TEFlex, Jerks_Flex1, Jerks_Flex2, Jerks_Flex3, Jerks_Flex4, Jerks_Flex5]
Jerks_Bench = [Jerks_Bench1, Jerks_Bench2, Jerks_Bench3, Jerks_IR]
Jerks_Score = 0
Jerks_ScoreDF = []
Jerks_BenchDF = []
for player in Jerks_Team:
    if player in df['Player'].values:  
        Jerks_Score += df.loc[df['Player'] == player, 'PPR'].iloc[0]
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        Jerks_ScoreDF.append(row)    
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
for player in Jerks_Bench:
    if player in df['Player'].values:  
        row = {'Player': player, 'Points': float(df.loc[df['Player'] == player, 'PPR'].iloc[0])}
        Jerks_BenchDF.append(row)
    elif player == '':
        row = {'Player': player, 'Points': 0}
        Jerks_BenchDF.append(row) 
    else:
        print(f"{player} not found in the DataFrame.")
        sys.exit()
print(f"\n Jerks Score = {round(Jerks_Score, 2)} \n")
pprint(Jerks_ScoreDF)
pprint(Jerks_BenchDF)



# File to save the outputs
#output_file = "dataframes_log.txt"

# Use append mode so each run adds to the same file
#with open(output_file, "a") as f:
#    f.write("\n" + "="*50 + "\n")
#    f.write(f"Run on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
#    f.write("="*50 + "\n\n")
    
#    f.write("DataFrame 1:\n")
#    f.write(df1.to_string(index=False))  # Convert DataFrame to text
#    f.write("\n\nDataFrame 2:\n")
#    f.write(df2.to_string(index=False))
#    f.write("\n\n")

