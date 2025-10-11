from Weekly_Webpage_Creator import All_DataFrames


SuperFlex = All_DataFrames["SuperFlex"]
GC_Total = []
Noche_Total = []
Paint_Total = []
Jerks_Total = []
n = 0
while n < 10:

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





print(f"'GC Score    =', {GC_Total.mean().round(2)}\n, 'Noche Score =', {Noche_Total.mean().round(2)}\n, 'Paint Score =', {Paint_Total.mean().round(2)}\n, 'Jerks Score =', {Jerks_Total.mean().round(2)}")