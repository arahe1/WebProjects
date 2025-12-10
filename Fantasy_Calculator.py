import pandas as pd
import sys
import os

pd.set_option('display.max_columns', None)


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
GC_RB1 = 'Bucky Irving'
GC_RB2 = 'Alvin Kamara'
GC_TE = 'Darren Waller'
GC_Flex = 'Brian Thomas'
GC_Bench1 = 'Kyle Monangai'
GC_Bench2 = 'Bhashul Tuten'
GC_Bench3 = 'Parker Washington'
GC_Bench4 = 'Trey Benson'
GC_Bench5 = 'Kimani Vidal'
GC_IR = 'Braelon Allen'
GC_DEF_approx = 8.90
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
GC_Score = GC_Score + GC_DEF_approx
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
GC_FinalDF = {"GC Score": [GC_Score]}


#Noche Score
Noche_QB1 = 'Jared Goff'
Noche_WR1 = 'Justin Jefferson'
Noche_WR2 = "Ja'Marr Chase"
Noche_WR3 = 'Stefon Diggs'
Noche_RB1 = 'Kyren Williams'
Noche_RB2 = 'Devin Neal'
Noche_TE = 'Dalton Kincaid'
Noche_Flex = 'Jordan Mason'
Noche_SuperFlex = 'Bo Nix'
Noche_Bench1 = 'Dallas Goedert'
Noche_Bench2 = 'Kareem Hunt'
Noche_Bench3 = 'Alvin Kamara'
Noche_Bench4 = 'Cooper Kupp'
Noche_IR = ''
Noche_DEF_approx = 8.67
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
Noche_Score = Noche_Score + Noche_DEF_approx
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
Noche_FinalDF = {"Noche Score": [Noche_Score]}



#Paint Score
Paint_QB = 'Matthew Stafford'
Paint_WR1 = 'Puka Nacua'
Paint_WR2 = 'Jaxon Smith-Njigba'
Paint_WR3 = 'Nico Collins'
Paint_RB1 = 'Breece Hall'
Paint_RB2 = 'Jonathan Taylor'
Paint_TE = 'Dallas Goedert'
Paint_Flex = 'Christian Watson'
Paint_Bench1 = 'Brian Thomas'
Paint_Bench2 = 'Kimani Vidal'
Paint_Bench3 = 'Jared Goff'
Paint_Bench4 = 'Devin Neal'
Paint_Bench5 = 'Darren Waller'
Paint_IR = 'Trey Benson'
Paint_K_approx = 12.81
Paint_DEF_approx = 14.70
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
Paint_Score = Paint_Score + Paint_K_approx + Paint_DEF_approx
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
Paint_FinalDF = {"Paint Score": [Paint_Score]}



#Jerks Score
Jerks_QB1 = 'Jaxson Dart'
Jerks_QB2 = 'C.J. Stroud'
Jerks_WR1 = 'Xavier Worthy'
Jerks_WR2 = 'Stefon Diggs'
Jerks_WR3 = 'Marvin Harrison Jr.'
Jerks_RB1 = 'Jahmyr Gibbs'
Jerks_RB2 = 'James Cook'
Jerks_TEFlex = 'Brock Bowers'
Jerks_Flex1 = "D'Andre Swift"
Jerks_Flex2 = 'Breece Hall'
Jerks_Flex3 = 'Devin Neal'
Jerks_Flex4 = 'Brenton Strange'
Jerks_Flex5 = 'Alec Pierce'
Jerks_Bench1 = 'Jayden Daniels'
Jerks_Bench2 = 'Quentin Johnston'
Jerks_Bench3 = 'Jalen Wright'
Jerks_IR = 'Trey Benson'
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
Jerks_FinalDF = {"Jerks Score": [Jerks_Score]}



dfs = {"GC Starters": pd.DataFrame(GC_ScoreDF),
       "GC Score": pd.DataFrame(GC_FinalDF),
       "GC Bench": pd.DataFrame(GC_BenchDF),
       "Noche Starters": pd.DataFrame(Noche_ScoreDF), 
       "Noche Score": pd.DataFrame(Noche_FinalDF),
       "Noche Bench": pd.DataFrame(Noche_BenchDF),
       "Paint Starters": pd.DataFrame(Paint_ScoreDF),
       "Paint Score": pd.DataFrame(Paint_FinalDF),
       "Paint Bench": pd.DataFrame(Paint_BenchDF),
       "Jerks Starters": pd.DataFrame(Jerks_ScoreDF),
       "Jerks Score": pd.DataFrame(Jerks_FinalDF),
       "Jerks Bench": pd.DataFrame(Jerks_BenchDF)}

full_path = os.path.join('CSVs', 'FantasyTeams.csv')

with open(full_path, "w") as f:
    for name, df in dfs.items():
        print(f"--- {name} ---", file=f)  # header from dict key
        print(df, file=f)
        print("\n", file=f)


