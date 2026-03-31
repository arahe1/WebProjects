import pandas as pd
import os
from collections import defaultdict
import numpy as np
import requests
from bs4 import BeautifulSoup
import unicodedata


#NFL Scripts

def importstats(csv): #imports CSV's via list and organizes them appropriately
    Dataframes=[]

    if not isinstance(csv, list):
        raise TypeError("Expected a List of CSV Files")
    
    for file in csv:
        if not isinstance(file, str):
            raise TypeError(f"List should contain strings of CSV file names. Got {type(file)}: {file}")
        if not file.lower().endswith('.csv'):
            raise ValueError(f"File is not a CSV file: {file}")
        if not os.path.exists(file):
            raise ValueError(f"File not found: {file}")

    for ele in csv:
        importer = pd.read_csv(ele, quotechar="'")
        Dataframes.append(importer)
    for i, df in enumerate(Dataframes):
        df.columns = df.columns.str.replace('"', '', regex=False)
        df['Rk'] = df['Rk'].str.replace('"', '', regex=False)
        df = df.drop(['Rk', 'Day', 'Date', 'Unnamed: 12', 'Opp', 'Result', 'Att', 'Att.1', 'Tgt', 'G#', 'Week','OffSnp'], axis=1)
        df = df.rename(columns={'1D': 'Rush1D', '1D.1': 'Rec1D', 'OffSnp.1': 'OffSnp', 'Att.2': 'PassAtt','TD': 'PassTD', 'Yds': 'PassYds', 'Y/A': 'PassY/A', 'Yds.1': 'SackYds', 'Succ%': 'PassSucc%', 'Att.3': 'RushAtt','TD.1': 'RushTD', 'Yds.2': 'RushYds', 'Y/A/1': 'RushY/A', 'Succ%.1': 'RushSucc%', 'Tgt.1': 'Tgt', 'Yds.3': 'RecYds', 'TD.2': 'RecTD', 'Succ%.2': 'RecSucc%'})

        Dataframes[i] = df


    return Dataframes


def schedulemaker(csv):
    if not isinstance(csv, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv)}: {csv}")
    if not csv.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv}")
    if not os.path.exists(csv):
        raise ValueError(f"File not found: {csv}")
    
    #NFL Schedule
    Schedule = pd.read_csv(csv)
    Schedule = Schedule.map(lambda x: x.replace('@', '') if isinstance(x, str) else x)

    #Conform to Stathead Labels
    Schedule = Schedule.map(lambda x: x.replace('GB', 'GNB') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('KC', 'KAN') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('LV', 'LVR') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('NO', 'NOR') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('NE', 'NWE') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('SF', 'SFO') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('TB', 'TAM') if isinstance(x, str) else x)
    return Schedule


def totalstatcombiner(dflist):
    Combined = pd.DataFrame()
    Total_Stats = pd.DataFrame()
    if not isinstance(dflist, list):
        raise TypeError("Expected a List of dataframes Files")
    
    for file in dflist:
        if not isinstance(file, pd.DataFrame):
            raise TypeError(f"List should contain strings of dataframes. Got {type(file)}: {file}")

    Combined = pd.concat(dflist, ignore_index=True)
    latest_rows = Combined.groupby("Player").last().reset_index()
    latest_col = latest_rows[["Player", "Team"]]
    Filtered = Combined.merge(latest_col, on=["Player", "Team"], how="inner")
    Numeric = Filtered.groupby("Player", as_index=False).sum(numeric_only=True)
    NonNumeric = latest_rows.drop(columns=Numeric.columns[1:], errors="ignore")
    Total_Stats = Numeric.merge(NonNumeric, on="Player")

    #Combined = pd.concat(dflist, ignore_index=True)
    #Numeric_Part = Combined.groupby(['Player', 'Team'], as_index=False).sum(numeric_only=True)
    #Non_Numeric_Part = Combined.groupby('Player', as_index=False).first(numeric_only=False).drop(columns=Numeric_Part.columns[1:])
    #Non_Numeric_Part = Combined.groupby(['Player', 'Team'], as_index=False).agg({'Team': 'last'})
    #Total_Stats = pd.merge(Numeric_Part, Non_Numeric_Part, on='Player')
    #Total_Stats = pd.merge(Numeric_Part, Non_Numeric_Part, on=['Player', 'Team'], how='left')

    return Total_Stats


def individualtotals(dflist):
    
    if not isinstance(dflist, list):
        raise TypeError("Expected a List of dataframes Files")

    # Collect totals ONLY for games the player played in

    # Initialize a list to collect results
    totals = []
    #teamtotals = []

    # Name of the column with player names
    name_col = "Player"  

    # Use a set to collect unique names
    unique_names = set()

    for df in dflist:
        unique_names.update(df[name_col].dropna().unique())

    # Convert back to list if needed
    unique_names_list = list(unique_names)

    # Loop through each player in unique_names_list
    for player in unique_names_list:
        total_ind_pass_att = 0  
        total_ind_pass_yards = 0
        total_ind_pass_td = 0
        total_ind_targets = 0
        total_ind_rec = 0
        total_ind_rec_yards = 0
        total_ind_rec_td = 0
        total_ind_rush_att = 0
        total_ind_rush_yards = 0
        total_ind_rush_td = 0

        ind_total_PA = 0
        ind_total_PY = 0
        ind_total_PT = 0
        ind_total_T = 0
        ind_total_R = 0
        ind_total_RY = 0
        ind_total_RT = 0
        ind_total_Ru = 0
        ind_total_RuY = 0
        ind_total_RuT = 0
        
        for df in dflist:
            if player in df['Player'].values:
                # Get the player's team (assumes 1 team per player per df)
                player_team = df.loc[df['Player'] == player, 'Team'].iloc[0]

                ind_total_PA = df.loc[df['Team'] == player_team, 'PassAtt'].sum()
                ind_total_PY = df.loc[df['Team'] == player_team, 'PassYds'].sum()
                ind_total_PT = df.loc[df['Team'] == player_team, 'PassTD'].sum()
                ind_total_T = df.loc[df['Team'] == player_team, 'Tgt'].sum()
                ind_total_R = df.loc[df['Team'] == player_team, 'Rec'].sum()
                ind_total_RY = df.loc[df['Team'] == player_team, 'RecYds'].sum()
                ind_total_RT = df.loc[df['Team'] == player_team, 'RecTD'].sum()
                ind_total_Ru = df.loc[df['Team'] == player_team, 'RushAtt'].sum()
                ind_total_RuY = df.loc[df['Team'] == player_team, 'RushYds'].sum()
                ind_total_RuT = df.loc[df['Team'] == player_team, 'RushTD'].sum()

                total_ind_pass_att += ind_total_PA
                total_ind_pass_yards += ind_total_PY
                total_ind_pass_td += ind_total_PT
                total_ind_targets += ind_total_T
                total_ind_rec += ind_total_R
                total_ind_rec_yards += ind_total_RY
                total_ind_rec_td += ind_total_RT
                total_ind_rush_att += ind_total_Ru
                total_ind_rush_yards += ind_total_RuY
                total_ind_rush_td += ind_total_RuT

        # Save result
        totals.append({'Player': player, 'TeamTotalPassAtt': total_ind_pass_att, 'TeamTotalPassYds': total_ind_pass_yards, 'TeamTotalPassTD': total_ind_pass_td, 'TeamTotalTgt': total_ind_targets , 'TeamTotalRec': total_ind_rec, 'TeamTotalRecYds': total_ind_rec_yards, 'TeamTotalRecTD': total_ind_rec_td, 'TeamTotalRushAtt': total_ind_rush_att, 'TeamTotalRushYds': total_ind_rush_yards, 'TeamTotalRushTD': total_ind_rush_td})

    # Create the final result DataFrame
    IndividualTotals = pd.DataFrame(totals)
    return IndividualTotals


def usefulstats(dflist, week, schedule, totalstats, individualtotals):
    if not isinstance(dflist, list):
        raise TypeError("Expected a List of dataframes Files")
    
    for file in dflist:
        if not isinstance(file, pd.DataFrame):
            raise TypeError(f"List should contain strings of dataframes. Got {type(file)}: {file}")
        
    if not isinstance(week, int):
        raise TypeError("int required for Week number")
    
    # Set up Useful Stats Dataframe columns
    Usefulcolumns = ['Player', 'Team', 'Opp', 'Week', 'Pos.', 'G', 'PassAtt', 'PassAttStDev', 'Cmp', 'IndComp%', 'CompStDev', 'TeamComp%', 'PassYds', 'PassYdsStDev', 'PassYds%', 'PassTD', 'PassTDStDev', 'PassTD%', 'Int', 'Tgt', 'TgtStDev','Rec', 'IndCatch%', 'CatStDev', 'TmCatch%', 'RecYds', 'RecYdsStDev', 'RecYds%', 'RecTD', 'RecTDStDev', 'RecTD%', 'RushAtt', 'RushStDev', 'Rush%', 'RushYds', 'RushYdsStDev', 'RushYds%', 'RushTD', 'RushTDStDev', 'RushTD%', ]
    Useful = pd.DataFrame(columns=Usefulcolumns)

    # Pre-map Opponents for quick lookup
    schedule_map = {row[0]: row[week] for row in schedule.itertuples(index=False)}

    # Pre-fill columns from Total_Stats if they exist
    for col in Useful.columns:
        if col in totalstats.columns:
            Useful[col] = totalstats[col]


    # Initialize containers for computed values
    stat_fields = ['PassAtt', 'Cmp', 'PassYds', 'PassTD', 'Int', 'Tgt', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']

    # Create per-player stat collections
    player_stats = defaultdict(lambda: defaultdict(list))
    player_games_played = defaultdict(int)

    # Precompute all stats from all DataFrames
    for df in dflist:
        if 'Player' not in df.columns:
            continue

        for row in df.itertuples(index=False):
            player = getattr(row, 'Player')

            player_games_played[player] += 1

            for stat in stat_fields:
                if hasattr(row, stat):
                    val = getattr(row, stat)
                    if pd.notnull(val):
                        player_stats[player][stat].append(val)

    # Now update Useful efficiently
    for i, row in Useful.iterrows():
        player = row['Player']
        team = row['Team']

        # Opponent from map
        Useful.at[i, 'Opp'] = schedule_map.get(team, None)

        # Games played
        Useful.at[i, 'G'] = player_games_played.get(player, 0)

        # Standard Deviations
        for stat in stat_fields:
            values = player_stats[player].get(stat, [])
            if len(values) >= 2:
                stdev = np.std(values, ddof=1)
            else:
                stdev = 0

            # Map stat name to your column names in Useful
            stdev_col_map = {
                'PassAtt': 'PassAttStDev',
                'Cmp': 'CompStDev',
                'PassYds': 'PassYdsStDev',
                'PassTD': 'PassTDStDev',
                'Tgt': 'TgtStDev',
                'Rec': 'CatStDev',
                'RecYds': 'RecYdsStDev',
                'RecTD': 'RecTDStDev',
                'RushAtt': 'RushStDev',
                'RushYds': 'RushYdsStDev',
                'RushTD': 'RushTDStDev',
            }

            if stat in stdev_col_map:
                Useful.at[i, stdev_col_map[stat]] = stdev


    Useful = Useful.set_index('Player')
    individualtotals = individualtotals.set_index('Player')

    # Update Individual Completion Percentage
    Useful['IndComp%'] = np.where(Useful['PassAtt'] != 0, (Useful['Cmp'] / Useful['PassAtt']), 0)

    # Update Individual Catch Percentage
    Useful['IndCatch%'] = np.where(Useful['Tgt'] != 0, (Useful['Rec'] / Useful['Tgt']), 0)

    # Update Team Comp Percentage
    Useful['TeamComp%'] = np.where(
        individualtotals['TeamTotalPassAtt'] != 0, (Useful['Cmp'] / individualtotals['TeamTotalPassAtt']), 0)

    # Update Team Pass Yards Percentage
    Useful['PassYds%'] = np.where(
        individualtotals['TeamTotalPassYds'] != 0, (Useful['PassYds'] / individualtotals['TeamTotalPassYds']), 0)

    # Update Team Pass TD Percentage
    Useful['PassTD%'] = np.where(
        individualtotals['TeamTotalPassTD'] != 0, (Useful['PassTD'] / individualtotals['TeamTotalPassTD']), 0)
    Useful['PassTD%'] = Useful['PassTD%'].fillna(0)

    # Update Team Catch Percentage
    Useful['TmCatch%'] = np.where(
        individualtotals['TeamTotalRec'] != 0, (Useful['Rec'] / individualtotals['TeamTotalRec']), 0)

    # Update Team Receiving Yards Percentage
    Useful['RecYds%'] = np.where(
        individualtotals['TeamTotalRecYds'] != 0, (Useful['RecYds'] / individualtotals['TeamTotalRecYds']), 0)

    # Update Team Receiving TD Percentage
    Useful['RecTD%'] = np.where(
        individualtotals['TeamTotalRecTD'] != 0, (Useful['RecTD'] / individualtotals['TeamTotalRecTD']), 0)
    Useful['RecTD%'] = Useful['RecTD%'].fillna(0)

    # Update Team Rush Percentage
    Useful['Rush%'] = np.where(
        individualtotals['TeamTotalRushAtt'] != 0, (Useful['RushAtt'] / individualtotals['TeamTotalRushAtt']), 0)

    # Update Team Rush Yard Percentage
    Useful['RushYds%'] = np.where(
        individualtotals['TeamTotalRushYds'] != 0, (Useful['RushYds'] / individualtotals['TeamTotalRushYds']), 0)

    # Update Team Rush TD Percentage
    Useful['RushTD%'] = np.where(
        individualtotals['TeamTotalRushTD'] != 0, (Useful['RushTD'] / individualtotals['TeamTotalRushTD']), 0)
    Useful['RushTD%'] = Useful['RushTD%'].fillna(0)

    Useful['Week'] = week

    Useful = Useful.reset_index()

    return Useful


def teamtotals(dflist, schedule):
       # Initialize a list to collect results
    teamtotals = []

    # Loop through each player in Useful
    for team in schedule['Team']:
        total_team_completions = 0  # Total sum across all DataFrames
        total_team_pass_yards = 0
        total_team_pass_td = 0
        total_team_rec = 0
        total_team_rec_yards = 0
        total_team_rec_td = 0
        total_team_rush_att = 0
        total_team_rush_yards = 0
        total_team_rush_td = 0

        for df in dflist:
            #if player in df['Player'].values:
                # Get the player's team (assumes 1 team per player per df)
            #team = df.loc[df['Team'] == team, 'Team'].iloc[0]
            matching_team = df.loc[df['Team'] == team, 'Team']
            if not matching_team.empty:
                team = matching_team.iloc[0]  # update only if found
            else:
                pass  # team stays as the last found

            # Sum Cmp for all players on the same team
            team_total_C = df.loc[df['Team'] == team, 'Cmp'].sum()
            team_total_PY = df.loc[df['Team'] == team, 'PassYds'].sum()
            team_total_PT = df.loc[df['Team'] == team, 'PassTD'].sum()
            team_total_R = df.loc[df['Team'] == team, 'Rec'].sum()
            team_total_RY = df.loc[df['Team'] == team, 'RecYds'].sum()
            team_total_RT = df.loc[df['Team'] == team, 'RecTD'].sum()
            team_total_Ru = df.loc[df['Team'] == team, 'RushAtt'].sum()
            team_total_RuY = df.loc[df['Team'] == team, 'RushYds'].sum()
            team_total_RuT = df.loc[df['Team'] == team, 'RushTD'].sum()

            total_team_completions += team_total_C
            total_team_pass_yards += team_total_PY
            total_team_pass_td += team_total_PT
            total_team_rec += team_total_R
            total_team_rec_yards += team_total_RY
            total_team_rec_td += team_total_RT
            total_team_rush_att += team_total_Ru
            total_team_rush_yards += team_total_RuY
            total_team_rush_td += team_total_RuT

        # Save result
        teamtotals.append({'Team': team, 'CmpAAV': total_team_completions, 'PassYdsAAV': total_team_pass_yards, 'PassTDAAV': total_team_pass_td, 'RecAAV': total_team_rec, 'RecYdsAAV': total_team_rec_yards, 'RecTDAAV': total_team_rec_td, 'RushAttAAV': total_team_rush_att, 'RushYdsAAV': total_team_rush_yards, 'RushTDAAV': total_team_rush_td})

    TeamTotals = pd.DataFrame(teamtotals)

    for column in TeamTotals.columns[1:]:
        row_index=0
        
        if (df.iloc[row_index, :len(dflist)] == 'BYE').any():
            TeamTotals[column] = (TeamTotals[column] - TeamTotals[column].mean())/(len(dflist-1))
        else:
            TeamTotals[column] = (TeamTotals[column] - TeamTotals[column].mean())/len(dflist)

    return TeamTotals


def weeklySuperFlexdataframe(useful, teamtotals):

    #Simulate 10,000 games and average for predictions
    n_simulations = 10000
    team_stats = teamtotals.set_index('Team').to_dict('index')

    statcolumns = ['Player', 'Team', 'Pos.', 'PPR', 'STD', 'PassYds', 'PassTD', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    SuperFlex = pd.DataFrame(columns=statcolumns)

    #Populate Superflex with Player names
    SuperFlex['Player'] = useful['Player']
    SuperFlex['Team'] = useful['Team']
    SuperFlex['Pos.'] = useful['Pos.']

    players = []

    predictedrushes = []
    predictedrushyards = []
    predictedrushtds = []

    predictedreceptions = []
    predictedreceivingyards = []
    predictedreceivingtds = []

    predictedpassingyards = []
    predictedpassingtds = []

    pprs = []
    stds = []

    for i, row in useful.iterrows():
        opp = row['Opp']
        rand1 = np.random.uniform(-2, 2, n_simulations)
        rand2 = np.random.uniform(-2, 2, n_simulations)
        rand3 = np.random.uniform(-2, 2, n_simulations)
        rand4 = np.random.uniform(-2, 2, n_simulations)
        rand5 = np.random.uniform(-2, 2, n_simulations)
        rand6 = np.random.uniform(-2, 2, n_simulations)
        rand7 = np.random.uniform(-2, 2, n_simulations)
        rand8 = np.random.uniform(-2, 2, n_simulations)
        if opp == 'BYE':
            team = 'None'
            rushes = np.zeros(n_simulations)
            rushyards = np.zeros(n_simulations)
            rushtds= np.zeros(n_simulations)

            receptions = np.zeros(n_simulations)
            receivingyards = np.zeros(n_simulations)
            receivingtds = np.zeros(n_simulations)

            passingyards = np.zeros(n_simulations)
            passingtds = np.zeros(n_simulations)
            
        else:
            team = team_stats[opp]

            # Simulations
            rushes = (row['RushAtt'] / row['G']) + row['RushStDev'] * rand1 + team['RushAttAAV'] * row['Rush%']
            rushyards = (row['RushYds'] / row['G']) + row['RushYdsStDev'] * rand2 + team['RushYdsAAV'] * row['RushYds%']
            rushtds = (row['RushTD'] / row['G']) + row['RushTDStDev'] * rand3 + team['RushTDAAV'] * row['RushTD%']

            receptions = (row['Tgt'] / row['G']) * row['IndCatch%'] + row['TgtStDev'] * row['IndCatch%'] * rand4 + team['RecAAV'] * row['TmCatch%']
            receivingyards = (row['RecYds'] / row['G']) + row['RecYdsStDev'] * rand5 + team['RecYdsAAV'] * row['RecYds%']
            receivingtds = (row['RecTD'] / row['G']) + row['RecTDStDev'] * rand6 + team['RecTDAAV'] * row['RecTD%']

            passingyards = (row['PassYds'] / row['G']) + row['PassYdsStDev'] * rand7 + team['PassYdsAAV'] * row['PassYds%']
            passingtds = (row['PassTD'] / row['G']) + row['PassTDStDev'] * rand8 + team['PassTDAAV'] * row['PassTD%']

        players.append(row['Player'])

        predictedrushes.append(np.clip(np.round(rushes.mean()).astype(int), 0, None))
        predictedrushyards.append(np.clip(np.round(rushyards.mean()).astype(int), 0, None))
        predictedrushtds.append(np.clip(np.round(rushtds.mean(),1), 0, None))

        predictedreceptions.append(np.clip(np.round(receptions.mean()).astype(int), 0, None))
        predictedreceivingyards.append(np.clip(np.round(receivingyards.mean()).astype(int), 0, None))
        predictedreceivingtds.append(np.clip(np.round(receivingtds.mean(),1), 0, None))

        predictedpassingyards.append(np.clip(np.round(passingyards.mean()).astype(int), 0, None))
        predictedpassingtds.append(np.clip(np.round(passingtds.mean(),1), 0, None))
        

        # Fantasy scoring
        ppr = (
            np.round(rushyards.mean()).astype(int) / 10 +
            np.round(receivingyards.mean()).astype(int) / 10 +
            np.round(passingyards.mean()).astype(int) / 25 +
            np.round(receptions.mean()).astype(int) +
            (np.round(rushtds.mean(),1) + np.round(receivingtds.mean(),1)) * 6 +
            np.round(passingtds.mean(),1) * 4
        )
        pprs.append(ppr)

        std = (
            np.round(rushyards.mean()).astype(int) / 10 +
            np.round(receivingyards.mean()).astype(int) / 10 +
            np.round(passingyards.mean()).astype(int) / 25 +
            (np.round(rushtds.mean(),1) + np.round(receivingtds.mean(),1)) * 6 +
            np.round(passingtds.mean(),1) * 4
        )
        stds.append(std)

    SuperFlex['RushAtt'] = predictedrushes
    SuperFlex['RushYds'] = predictedrushyards
    SuperFlex['RushTD'] = predictedrushtds
    SuperFlex['Rec'] = predictedreceptions
    SuperFlex['RecYds'] = predictedreceivingyards
    SuperFlex['RecTD'] = predictedreceivingtds
    SuperFlex['PassYds'] = predictedpassingyards
    SuperFlex['PassTD'] = predictedpassingtds
    SuperFlex['PPR'] = pprs
    SuperFlex['STD'] = stds
    SuperFlex.iloc[:, 3:5] = SuperFlex.iloc[:, 3:5].apply(pd.to_numeric).round(1)


    return SuperFlex


def injuryremovalweekly(superflex):
    #Erasing Injured Players from DataFrames using ESPN

    # URL of the website you want to scrape
    url = 'https://www.espn.com/nfl/injuries'

    # Send an HTTP GET request to the URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/',  # optional, but can help
        'Accept-Language': 'en-US,en;q=0.9',
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    # Get all team name spans
    team_spans = soup.find_all("span", class_="injuries__teamName")

    # Get all tables (assumed in same order as teams)
    tables = soup.find_all("table")
    hurtplayers = []
    # Loop through team/table pairs
    for team_span, table in zip(team_spans, tables):

        # Extract headers
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]

        # Extract rows
        rows = table.find_all("tr")[1:]  # skip header row
        for row in rows:
            cols = row.find_all("td")
            if len(cols) != len(headers):
                continue  # skip malformed rows
            data = {}
            for i in range(len(headers)):
                # If it's a link (e.g. player name), get the text
                link = cols[i].find("a")
                text = link.get_text(strip=True) if link else cols[i].get_text(strip=True)
                data[headers[i]] = text
            hurtplayers.append(data)


    #List_All_Dataframes = [SuperFlex, Flex, WR, RB, TE, QB]

    IR_Players = [
        player['name']
        for player in hurtplayers
        if player.get('status') in ['Out', 'Injured Reserve']
    ]


    #print(IR_Players)
    #print(superflex.columns.tolist())
    #print(superflex['Player'].isin(IR_Players).value_counts())
    superflex = superflex[~superflex['Player'].isin(IR_Players)]
    #superflex.loc[superflex['Player'].isin(IR_Players), ~superflex.columns.isin(['Player', 'Team', 'Rank', 'Pos.'])] = 0
    #superflex.loc[superflex['Player'].isin(IR_Players), [c for c in superflex.columns if c not in ['Player', 'Team', 'Rank', 'Pos.']]] = 0

    #Useful = useful[~useful['Player'].isin(IR_Players)]
    #SuperFlex = SuperFlex[~SuperFlex['Player'].isin(IR_Players)]
    #Flex = Flex[~Flex['Player'].isin(IR_Players)]
    #WR = WR[~WR['Player'].isin(IR_Players)]
    #RB = RB[~RB['Player'].isin(IR_Players)]
    #TE = TE[~TE['Player'].isin(IR_Players)]
    #QB = QB[~QB['Player'].isin(IR_Players)]

    return superflex


def weeklyfinaldataframes(superflex):

    flexstatcolumns = ['Player', 'Team', 'Pos.', 'PPR', 'STD', 'PassYds', 'PassTD', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    statcolumns = ['Player', 'Team', 'PPR', 'STD', 'PassYds', 'PassTD', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    Flex = pd.DataFrame(columns=flexstatcolumns)
    WR = pd.DataFrame(columns=statcolumns)
    RB = pd.DataFrame(columns=statcolumns)
    TE = pd.DataFrame(columns=statcolumns)
    QB = pd.DataFrame(columns=statcolumns)

        #Populate Flex with Player names
    for i, row in superflex.iterrows():
        keywords = ['WR', 'RB', 'TE']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            Flex.at[i, 'Player'] = row['Player']

    #Populate WR with Player names
    for i, row in superflex.iterrows():
        keywords = ['WR']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            WR.at[i, 'Player'] = row['Player']

    #Populate RB with Player names
    for i, row in superflex.iterrows():
        keywords = ['RB']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            RB.at[i, 'Player'] = row['Player']

    #Populate TE with Player names
    for i, row in superflex.iterrows():
        keywords = ['TE']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            TE.at[i, 'Player'] = row['Player']

    #Populate QB with Player names
    for i, row in superflex.iterrows():
        keywords = ['QB']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            QB.at[i, 'Player'] = row['Player']


    for col in superflex.columns:
        if col != 'Player' and col in Flex.columns:
            Flex[col] = Flex['Player'].map(superflex.set_index('Player')[col])

    for col in superflex.columns:
        if col != 'Player' and col in WR.columns:
            WR[col] = WR['Player'].map(superflex.set_index('Player')[col])

    for col in superflex.columns:
        if col != 'Player' and col in RB.columns:
            RB[col] = RB['Player'].map(superflex.set_index('Player')[col])

    for col in superflex.columns:
        if col != 'Player' and col in TE.columns:
            TE[col] = TE['Player'].map(superflex.set_index('Player')[col])

    for col in superflex.columns:
        if col != 'Player' and col in QB.columns:
            QB[col] = QB['Player'].map(superflex.set_index('Player')[col])


    superflex['Rank'] = range(1, len(superflex) + 1)
    Flex['Rank'] = range(1, len(Flex) + 1)
    WR['Rank'] = range(1, len(WR) + 1)
    RB['Rank'] = range(1, len(RB) + 1)
    TE['Rank'] = range(1, len(TE) + 1)
    QB['Rank'] = range(1, len(QB) + 1)

    cols = ['Rank'] + [col for col in superflex.columns if col != 'Rank']
    superflex = superflex[cols]

    cols = ['Rank'] + [col for col in Flex.columns if col != 'Rank']
    Flex = Flex[cols]

    cols = ['Rank'] + [col for col in WR.columns if col != 'Rank']
    WR = WR[cols]

    cols = ['Rank'] + [col for col in RB.columns if col != 'Rank']
    RB = RB[cols]

    cols = ['Rank'] + [col for col in TE.columns if col != 'Rank']
    TE = TE[cols]

    cols = ['Rank'] + [col for col in QB.columns if col != 'Rank']
    QB = QB[cols]

    All_DataFrames = {'SuperFlex': superflex, 'Flex': Flex, 'WR': WR, 'RB': RB, 'TE': TE, 'QB': QB}

    

    return All_DataFrames


def weeklyhtml(alldataframes, week):
    #html_dict = {}

    for name, df in alldataframes.items():

        html_string = df.to_html(classes='display', index=False).replace('class="dataframe display"', 'class="display"')

        # Full HTML file with sorting and ALL rows shown
        html_script = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>{name} Stats</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="icon" type="image/png" sizes="96x96" href="/WebProjects/images/favicon-96x96.png" />
        <link rel="icon" type="image/svg+xml" href="/WebProjects/images/favicon.svg" />
        <link rel="shortcut icon" href="/WebProjects/images/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/WebProjects/images/apple-touch-icon.png" />
        <meta name="apple-mobile-web-app-title" content="MyWebSit" />
        <link rel="manifest" href="/WebProjects/images/site.webmanifest" />

        <link rel="stylesheet" href="/WebProjects/style.css">


        </head>
        <body>

        <div class="topnav">
        <a href="/WebProjects/index.html">Home</a>
            <div class="dropdown">
            <button class="dropbtn active">Football
                <i class="fa fa-caret-down"></i>
            </button>
            <div class="dropdown-content">
                <a href="/WebProjects/WeeklyPred_html/SuperFlex.html">Weekly Predictions</a>
                <a href="/WebProjects/ROS_html/Rest Of Season.html">Rest of Season Predictions</a>
                <a href="/WebProjects/WeeklyScores_html/Weekly Game Predictions.html">Weekly Game Predictions</a>
                <a href="/WebProjects/Dominance_html/QBDom.html">Offensive Focus</a>
            </div>
            </div>
            <div class="dropdown">
            <button class="dropbtn">Baseball
                <i class="fa fa-caret-down"></i>
            </button>
            <div class="dropdown-content">
                <a href="/WebProjects/PreseasonMLBHittingPredictions.html">MLB Preseason Hitting Predictions</a>
                <a href="/WebProjects/PreseasonMLBPitchingPredictions.html">MLB Preseason Pitching Predictions</a>
            </div>
            </div>
        <a href="/WebProjects/Fitness_html/fitness.html">Fitness</a>
        <a href="/WebProjects/about.html">About</a>
        </div>


        <img src="/WebProjects/images/Banner_Logo.png" alt="Header Image" class="header-img">

        <h1>Week {week} {name} Predictions</h1>

        <div class="topnav">
        <input type="text" id="searchBar" placeholder="Search...">
        </div>
        
        <div class="topnav">
        <a {"class='active'" if name == "SuperFlex" else ""} href="SuperFlex.html">SuperFlex</a>
        <a {"class='active'" if name == "Flex" else ""} href="Flex.html">Flex</a>
        <a {"class='active'" if name == "QB" else ""} href="QB.html">QB</a>
        <a {"class='active'" if name == "WR" else ""} href="WR.html">WR</a>
        <a {"class='active'" if name == "RB" else ""} href="RB.html">RB</a>
        <a {"class='active'" if name == "TE" else ""} href="TE.html">TE</a>

        </div>

        


        {html_string}

        <script>
        function getCellValue(row, index) {{
            return row.cells[index].textContent.trim();
        }}

        function comparer(index, asc) {{
            return function(a, b) {{
            const v1 = getCellValue(a, index);
            const v2 = getCellValue(b, index);

            const num1 = parseFloat(v1);
            const num2 = parseFloat(v2);
            const bothNumbers = !isNaN(num1) && !isNaN(num2);

            if (bothNumbers) {{
                return asc ? num1 - num2 : num2 - num1;
            }} else {{
                return asc ? v1.localeCompare(v2) : v2.localeCompare(v1);
            }}
            }};
        }}

        document.addEventListener("DOMContentLoaded", function () {{
            document.querySelectorAll("th").forEach(function (th, index) {{
            let ascending = true;
            if (index === 0) return;
            th.addEventListener("click", function () {{
                const table = th.closest("table");
                const tbody = table.querySelector("tbody");
                const rows = Array.from(tbody.querySelectorAll("tr"));
                rows.sort(comparer(index, ascending));
                //rows.forEach(row => tbody.appendChild(row));
                rows.forEach((row, i) => {{
                    row.cells[0].textContent = i + 1; // Reset Rank to match new row position
                    tbody.appendChild(row);
                }});
                ascending = !ascending;
            }});
            }});
        }});
        </script>

        

        <script>
        const searchBar = document.getElementById('searchBar');
        const table = document.querySelector('table');
        const rows = table.getElementsByTagName('tr');

        searchBar.addEventListener('keyup', function () {{
            const searchText = searchBar.value.toLowerCase();

            for (let i = 1; i < rows.length; i++) {{
            const row = rows[i];
            const rowText = row.textContent.toLowerCase();
            row.style.display = rowText.includes(searchText) ? '' : 'none';
            }}
        }});
        </script>

        

        </body>
        </html>
        """

        # Save to HTML file
        with open(f"WeeklyPred_html/{name}.html", "w", encoding="utf-8") as f:
            f.write(html_script)


def injuryremovalros(ros):
    #Erasing Injured Players from DataFrames using ESPN

    # URL of the website you want to scrape
    url = 'https://www.espn.com/nfl/injuries'

    # Send an HTTP GET request to the URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/',  # optional, but can help
        'Accept-Language': 'en-US,en;q=0.9',
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    # Get all team name spans
    team_spans = soup.find_all("span", class_="injuries__teamName")

    # Get all tables (assumed in same order as teams)
    tables = soup.find_all("table")
    hurtplayers = []
    # Loop through team/table pairs
    for team_span, table in zip(team_spans, tables):

        # Extract headers
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]

        # Extract rows
        rows = table.find_all("tr")[1:]  # skip header row
        for row in rows:
            cols = row.find_all("td")
            if len(cols) != len(headers):
                continue  # skip malformed rows
            data = {}
            for i in range(len(headers)):
                # If it's a link (e.g. player name), get the text
                link = cols[i].find("a")
                text = link.get_text(strip=True) if link else cols[i].get_text(strip=True)
                data[headers[i]] = text
            hurtplayers.append(data)


    #List_All_Dataframes = [SuperFlex, Flex, WR, RB, TE, QB]

    IR_Players = [
        player['name']
        for player in hurtplayers
        if player.get('status') in ['Injured Reserve']
    ]


    #print(IR_Players)

    #ros.loc[ros['Player'].isin(IR_Players), ros.columns.difference(['Player', 'Team', 'Rank', 'Pos.'])] = 0
    ros.loc[ros['Player'].isin(IR_Players), [c for c in ros.columns if c not in ['Player', 'Team', 'Rank', 'Pos.']]] = 0
    
    #print(ros[ros['Player'] == 'Austin Ekeler'])
    
    
    #print(ros[ros['Player'].isin(IR_Players)])
    #Useful = useful[~useful['Player'].isin(IR_Players)]
    #SuperFlex = SuperFlex[~SuperFlex['Player'].isin(IR_Players)]
    #Flex = Flex[~Flex['Player'].isin(IR_Players)]
    #WR = WR[~WR['Player'].isin(IR_Players)]
    #RB = RB[~RB['Player'].isin(IR_Players)]
    #TE = TE[~TE['Player'].isin(IR_Players)]
    #QB = QB[~QB['Player'].isin(IR_Players)]

    return ros


def ROSdataframe(useful, teamtotals, week, schedule):

    statcolumns = ['Player', 'Team', 'Pos.', 'PPR', 'STD', 'PassYds', 'PassTD', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']

    # Prepare your output DataFrame
    ROS = pd.DataFrame()
    ROS['Player'] = useful['Player']
    ROS['Team'] = useful['Team']
    ROS['Pos.'] = useful['Pos.']

    stats = [col for col in statcolumns if col not in ['Player', 'Team', 'Pos.']]
    #stats = [col for col in statcolumns if col != 'Player']

    # Initialize projection columns to 0
    for stat in stats:
        ROS[stat] = 0

    #Simulate 10,000 games and average for predictions then add them for ROS
    n_simulations = 10000
    team_stats = teamtotals.set_index('Team').to_dict('index')


    for week in range(week, 18):

        players = []

        predictedrushes = []
        predictedrushyards = []
        predictedrushtds = []

        predictedreceptions = []
        predictedreceivingyards = []
        predictedreceivingtds = []

        predictedpassingyards = []
        predictedpassingtds = []

        pprs = []
        stds = []

        schedule_map = {row[0]: row[week] for row in schedule.itertuples(index=False)}
        for i, row in useful.iterrows():

            team = row['Team']
            opp = schedule_map.get(team, 'BYE')
            rand1 = np.random.uniform(-2, 2, n_simulations)
            rand2 = np.random.uniform(-2, 2, n_simulations)
            rand3 = np.random.uniform(-2, 2, n_simulations)
            rand4 = np.random.uniform(-2, 2, n_simulations)
            rand5 = np.random.uniform(-2, 2, n_simulations)
            rand6 = np.random.uniform(-2, 2, n_simulations)
            rand7 = np.random.uniform(-2, 2, n_simulations)
            rand8 = np.random.uniform(-2, 2, n_simulations)
            if opp == 'BYE':
                
                rushes = np.zeros(n_simulations)
                rushyards = np.zeros(n_simulations)
                rushtds= np.zeros(n_simulations)

                receptions = np.zeros(n_simulations)
                receivingyards = np.zeros(n_simulations)
                receivingtds = np.zeros(n_simulations)

                passingyards = np.zeros(n_simulations)
                passingtds = np.zeros(n_simulations)
                
            else:
                team = team_stats[opp]
                
                # Simulations
                rushes = (row['RushAtt'] / row['G']) + row['RushStDev'] * rand1 + team['RushAttAAV'] * row['Rush%']
                rushyards = (row['RushYds'] / row['G']) + row['RushYdsStDev'] * rand2 + team['RushYdsAAV'] * row['RushYds%']
                rushtds = (row['RushTD'] / row['G']) + row['RushTDStDev'] * rand3 + team['RushTDAAV'] * row['RushTD%']

                receptions = (row['Tgt'] / row['G']) * row['IndCatch%'] + row['TgtStDev'] * row['IndCatch%']* rand4 + team['RecAAV'] * row['TmCatch%']
                receivingyards = (row['RecYds'] / row['G']) + row['RecYdsStDev'] * rand5 + team['RecYdsAAV'] * row['RecYds%']
                receivingtds = (row['RecTD'] / row['G']) + row['RecTDStDev'] * rand6 + team['RecTDAAV'] * row['RecTD%']

                passingyards = (row['PassYds'] / row['G']) + row['PassYdsStDev'] * rand7 + team['PassYdsAAV'] * row['PassYds%']
                passingtds = (row['PassTD'] / row['G']) + row['PassTDStDev'] * rand8 + team['PassTDAAV'] * row['PassTD%']

            players.append(row['Player'])

            predictedrushes.append(np.clip(np.round(rushes.mean()).astype(int), 0, None))
            predictedrushyards.append(np.clip(np.round(rushyards.mean()).astype(int), 0, None))
            predictedrushtds.append(np.clip(np.round(rushtds.mean(),1), 0, None))

            predictedreceptions.append(np.clip(np.round(receptions.mean()).astype(int), 0, None))
            predictedreceivingyards.append(np.clip(np.round(receivingyards.mean()).astype(int), 0, None))
            predictedreceivingtds.append(np.clip(np.round(receivingtds.mean(),1), 0, None))

            predictedpassingyards.append(np.clip(np.round(passingyards.mean()).astype(int), 0, None))
            predictedpassingtds.append(np.clip(np.round(passingtds.mean(),1), 0, None))
            

            # Fantasy scoring
            ppr = (
                np.round(rushyards.mean()).astype(int) / 10 +
                np.round(receivingyards.mean()).astype(int) / 10 +
                np.round(passingyards.mean()).astype(int) / 25 +
                np.round(receptions.mean()).astype(int) +
                (np.round(rushtds.mean(),1) + np.round(receivingtds.mean(),1)) * 6 +
                np.round(passingtds.mean(),1) * 4
            )
            pprs.append(ppr)

            std = (
                np.round(rushyards.mean()).astype(int) / 10 +
                np.round(receivingyards.mean()).astype(int) / 10 +
                np.round(passingyards.mean()).astype(int) / 25 +
                (np.round(rushtds.mean(),1) + np.round(receivingtds.mean(),1)) * 6 +
                np.round(passingtds.mean(),1) * 4
            )
            stds.append(std)


        ROS['RushAtt'] += predictedrushes
        ROS['RushYds'] += predictedrushyards
        ROS['RushTD'] += predictedrushtds
        ROS['Rec'] += predictedreceptions
        ROS['RecYds'] += predictedreceivingyards
        ROS['RecTD'] += predictedreceivingtds
        ROS['PassYds'] += predictedpassingyards
        ROS['PassTD'] += predictedpassingtds
        ROS['PPR'] += pprs
        ROS['STD'] += stds
        ROS.iloc[:, 3:5] = ROS.iloc[:, 3:5].apply(pd.to_numeric).round(1)

    ROS['Team'] = useful['Team']

    return ROS


def rosfinaldataframes(ros):

    flexstatcolumns = ['Player', 'Team', 'PPR', 'STD', 'PassYds', 'PassTD', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    statcolumns = ['Player', 'Team', 'PPR', 'STD', 'PassYds', 'PassTD', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    Flex_ROS = pd.DataFrame(columns=flexstatcolumns)
    WR_ROS = pd.DataFrame(columns=statcolumns)
    RB_ROS = pd.DataFrame(columns=statcolumns)
    TE_ROS = pd.DataFrame(columns=statcolumns)
    QB_ROS = pd.DataFrame(columns=statcolumns)


        #Populate Flex with Player names
    for i, row in ros.iterrows():
        keywords = ['WR', 'RB', 'TE']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            Flex_ROS.at[i, 'Player'] = row['Player']

    #Populate WR with Player names
    for i, row in ros.iterrows():
        keywords = ['WR']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            WR_ROS.at[i, 'Player'] = row['Player']

    #Populate RB with Player names
    for i, row in ros.iterrows():
        keywords = ['RB']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            RB_ROS.at[i, 'Player'] = row['Player']

    #Populate TE with Player names
    for i, row in ros.iterrows():
        keywords = ['TE']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            TE_ROS.at[i, 'Player'] = row['Player']

    #Populate QB with Player names
    for i, row in ros.iterrows():
        keywords = ['QB']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            QB_ROS.at[i, 'Player'] = row['Player']

    for col in ros.columns:
        if col != 'Player' and col in Flex_ROS.columns:
            Flex_ROS[col] = Flex_ROS['Player'].map(ros.set_index('Player')[col])

    for col in ros.columns:
        if col != 'Player' and col in WR_ROS.columns:
            WR_ROS[col] = WR_ROS['Player'].map(ros.set_index('Player')[col])

    for col in ros.columns:
        if col != 'Player' and col in RB_ROS.columns:
            RB_ROS[col] = RB_ROS['Player'].map(ros.set_index('Player')[col])

    for col in ros.columns:
        if col != 'Player' and col in TE_ROS.columns:
            TE_ROS[col] = TE_ROS['Player'].map(ros.set_index('Player')[col])

    for col in ros.columns:
        if col != 'Player' and col in QB_ROS.columns:
            QB_ROS[col] = QB_ROS['Player'].map(ros.set_index('Player')[col])

    ros['Rank'] = range(1, len(ros) + 1)
    Flex_ROS['Rank'] = range(1, len(Flex_ROS) + 1)
    WR_ROS['Rank'] = range(1, len(WR_ROS) + 1)
    RB_ROS['Rank'] = range(1, len(RB_ROS) + 1)
    TE_ROS['Rank'] = range(1, len(TE_ROS) + 1)
    QB_ROS['Rank'] = range(1, len(QB_ROS) + 1)

    cols = ['Rank'] + [col for col in ros.columns if col != 'Rank']
    ros = ros[cols]

    cols = ['Rank'] + [col for col in Flex_ROS.columns if col != 'Rank']
    Flex_ROS = Flex_ROS[cols]

    cols = ['Rank'] + [col for col in WR_ROS.columns if col != 'Rank']
    WR_ROS = WR_ROS[cols]

    cols = ['Rank'] + [col for col in RB_ROS.columns if col != 'Rank']
    RB_ROS = RB_ROS[cols]

    cols = ['Rank'] + [col for col in TE_ROS.columns if col != 'Rank']
    TE_ROS = TE_ROS[cols]

    cols = ['Rank'] + [col for col in QB_ROS.columns if col != 'Rank']
    QB_ROS = QB_ROS[cols]


    All_DataFrames = {'Rest Of Season': ros, 'Flex ROS': Flex_ROS, 'WR ROS': WR_ROS, 'RB ROS': RB_ROS, 'TE ROS': TE_ROS, 'QB ROS': QB_ROS}


    return All_DataFrames


def roshtml(alldataframes):
    #html_dict = {}

    for name, df in alldataframes.items():

        html_string = df.to_html(classes='display', index=False).replace('class="dataframe display"', 'class="display"')

        # Full HTML file with sorting and ALL rows shown
        html_script = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>{name} Stats</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="icon" type="image/png" sizes="96x96" href="/WebProjects/images/favicon-96x96.png" />
        <link rel="icon" type="image/svg+xml" href="/WebProjects/images/favicon.svg" />
        <link rel="shortcut icon" href="/WebProjects/images/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/WebProjects/images/apple-touch-icon.png" />
        <meta name="apple-mobile-web-app-title" content="MyWebSit" />
        <link rel="manifest" href="/WebProjects/images/site.webmanifest" />

        <link rel="stylesheet" href="/WebProjects/style.css">


        </head>
        <body>

        <div class="topnav">
        <a href="/WebProjects/index.html">Home</a>
            <div class="dropdown">
            <button class="dropbtn active">Football
                <i class="fa fa-caret-down"></i>
            </button>
            <div class="dropdown-content">
                <a href="/WebProjects/WeeklyPred_html/SuperFlex.html">Weekly Predictions</a>
                <a href="/WebProjects/ROS_html/Rest Of Season.html">Rest of Season Predictions</a>
                <a href="/WebProjects/WeeklyScores_html/Weekly Game Predictions.html">Weekly Game Predictions</a>
                <a href="/WebProjects/Dominance_html/QBDom.html">Offensive Focus</a>
            </div>
            </div>
            <div class="dropdown">
            <button class="dropbtn">Baseball
                <i class="fa fa-caret-down"></i>
            </button>
            <div class="dropdown-content">
                <a href="/WebProjects/PreseasonMLBHittingPredictions.html">MLB Preseason Hitting Predictions</a>
                <a href="/WebProjects/PreseasonMLBPitchingPredictions.html">MLB Preseason Pitching Predictions</a>
            </div>
            </div>
        <a href="/WebProjects/Fitness_html/fitness.html">Fitness</a>
        <a href="/WebProjects/about.html">About</a>
        </div>
        

        <img src="/WebProjects/images/Banner_Logo.png" alt="Header Image" class="header-img">

        <h1>{name} Predictions</h1>

        <div class="topnav">
        <input type="text" id="searchBar" placeholder="Search...">
        </div>

        <div class="topnav">
        <a {"class='active'" if name == "Rest Of Season" else ""} href="Rest Of Season.html">ROS</a>
        <a {"class='active'" if name == "Flex ROS" else ""} href="Flex ROS.html">Flex ROS</a>
        <a {"class='active'" if name == "QB ROS" else ""} href="QB ROS.html">QB ROS</a>
        <a {"class='active'" if name == "WR ROS" else ""} href="WR ROS.html">WR ROS</a>
        <a {"class='active'" if name == "RB ROS" else ""} href="RB ROS.html">RB ROS</a>
        <a {"class='active'" if name == "TE ROS" else ""} href="TE ROS.html">TE ROS</a>

        </div>





        {html_string}

        <script>
        function getCellValue(row, index) {{
            return row.cells[index].textContent.trim();
        }}

        function comparer(index, asc) {{
            return function(a, b) {{
            const v1 = getCellValue(a, index);
            const v2 = getCellValue(b, index);

            const num1 = parseFloat(v1);
            const num2 = parseFloat(v2);
            const bothNumbers = !isNaN(num1) && !isNaN(num2);

            if (bothNumbers) {{
                return asc ? num1 - num2 : num2 - num1;
            }} else {{
                return asc ? v1.localeCompare(v2) : v2.localeCompare(v1);
            }}
            }};
        }}

        document.addEventListener("DOMContentLoaded", function () {{
            document.querySelectorAll("th").forEach(function (th, index) {{
            let ascending = true;
            if (index === 0) return;
            th.addEventListener("click", function () {{
                const table = th.closest("table");
                const tbody = table.querySelector("tbody");
                const rows = Array.from(tbody.querySelectorAll("tr"));
                rows.sort(comparer(index, ascending));
                //rows.forEach(row => tbody.appendChild(row));
                rows.forEach((row, i) => {{
                    row.cells[0].textContent = i + 1; // Reset Rank to match new row position
                    tbody.appendChild(row);
                }});
                ascending = !ascending;
            }});
            }});
        }});
        </script>

        

        <script>
        const searchBar = document.getElementById('searchBar');
        const table = document.querySelector('table');
        const rows = table.getElementsByTagName('tr');

        searchBar.addEventListener('keyup', function () {{
            const searchText = searchBar.value.toLowerCase();

            for (let i = 1; i < rows.length; i++) {{
            const row = rows[i];
            const rowText = row.textContent.toLowerCase();
            row.style.display = rowText.includes(searchText) ? '' : 'none';
            }}
        }});
        </script>

        

        </body>
        </html>
        """

        # Save to HTML file
        with open(f"ROS_html/{name}.html", "w", encoding="utf-8") as f:
            f.write(html_script)


def teamwinnerschedule(csv, week):
    if not isinstance(csv, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv)}: {csv}")
    if not csv.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv}")
    if not os.path.exists(csv):
        raise ValueError(f"File not found: {csv}")
    
    #NFL Schedule
    Schedule = pd.read_csv(csv)
    #Schedule = Schedule.map(lambda x: x.replace('@', '') if isinstance(x, str) else x)

    #Conform to Stathead Labels
    Schedule = Schedule.map(lambda x: x.replace('GB', 'GNB') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('KC', 'KAN') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('LV', 'LVR') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('NO', 'NOR') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('NE', 'NWE') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('SF', 'SFO') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('TB', 'TAM') if isinstance(x, str) else x)

    Week = 'W' + str(week)
    Schedule = Schedule[~Schedule[Week].str.contains("@", na=False)]
    Schedule = Schedule[~Schedule[Week].str.contains('BYE',na=False)]
    Schedule = Schedule[['Team', Week]]
    Schedule = Schedule.rename(columns={Week: "Opp"})

    return Schedule


def weeklyteamwinner(csv):
    Dataframes=[]

    if not isinstance(csv, list):
        raise TypeError("Expected a List of CSV Files")
    
    for file in csv:
        if not isinstance(file, str):
            raise TypeError(f"List should contain strings of CSV file names. Got {type(file)}: {file}")
        if not file.lower().endswith('.csv'):
            raise ValueError(f"File is not a CSV file: {file}")
        if not os.path.exists(file):
            raise ValueError(f"File not found: {file}")

    for ele in csv:
        importer = pd.read_csv(ele, quotechar="'")
        Dataframes.append(importer)
    for i, df in enumerate(Dataframes):
        df.columns = df.columns.str.replace('"', '', regex=False)
        df['Rk'] = df['Rk'].str.replace('"', '', regex=False)
        df = df.drop(['Rk', 'Day', 'Date', 'Result', 'Pts.1', 'PtsO.1', 'PtDif', 'PC', 'G#', 'Unnamed: 8', 'Opp'], axis=1)
        #df = df.rename(columns={'Unnamed: 8': 'HomeField'})

        Dataframes[i] = df


    return Dataframes


def teamuseful(dflist, week, schedule):

    # Pre-map Opponents for quick lookup
    schedule_map = {row[0]: row[week] for row in schedule.itertuples(index=False)}

    # Initialize containers for computed values
    stat_fields = ['Pts', 'PtsO']

    # Create per-player stat collections
    team_stats = defaultdict(lambda: defaultdict(list))
    team_games_played = defaultdict(int)

    # Add Useful DataFrame
    Useful = pd.DataFrame(columns=dflist[0].columns)
    Useful['Team'] = dflist[0]['Team']
    #Useful['Team'] = homefield['Team']
    #Useful['Opp'] = homefield['Opp']


    for df in dflist:
        if 'Team' not in df.columns:
            continue

        for row in df.itertuples(index=False):
            team = getattr(row, 'Team')

            team_games_played[team] += 1

            for stat in stat_fields:
                if hasattr(row, stat):
                    val = getattr(row, stat)
                    if pd.notnull(val):
                        team_stats[team][stat].append(val)

    # Now update Useful efficiently
    for i, row in Useful.iterrows():
        team = row['Team']

        # Opponent from map
        Useful.at[i, 'Opp'] = schedule_map.get(team, None)

        # Games played
        Useful.at[i, 'G'] = team_games_played.get(team, 0)


        # Standard Deviations
        for stat in stat_fields:
            values = team_stats[team].get(stat, [])
            ave = np.mean(values) if len(values) > 0 else 0
            if len(values) >= 2:
                stdev = np.std(values, ddof=1)
            else:
                stdev = 0
                

            # Map stat name to your column names in Useful
            stdev_col_map = {
                'Pts': 'PtsDev',
                'PtsO': 'PtsODev',
            }

            Useful.at[i,stat] = ave

            if stat in stdev_col_map:
                Useful.at[i, stdev_col_map[stat]] = stdev

            
            
    # Update Team Averages
    Useful['Week'] = week
    Useful['Pts'] = pd.to_numeric(Useful['Pts']).round(1)#.astype(str)
    Useful['PtsO'] = pd.to_numeric(Useful['PtsO']).round(1)#.astype(str)
    Useful['PtsDev'] = pd.to_numeric(Useful['PtsDev']).round(2)#.astype(str)
    Useful['PtsODev'] = pd.to_numeric(Useful['PtsODev']).round(2)#.astype(str) 




    return Useful


def teammc(useful,homefield):
    #Simulate 10,000 games and average for predictions
    n_simulations = 10000
    opp_stats = useful.set_index('Team').to_dict('index')

    statcolumns = ['Team', 'Opp', 'Winner', 'Points For', 'Points Against', 'Total', 'Home Spread']
    FinalScores = pd.DataFrame(columns=statcolumns)

    #Populate Superflex with Player names
    FinalScores['Team'] = useful['Team']
    FinalScores['Opp'] = useful['Opp']

    Points_For = []


    ave = useful['PtsO'].mean()
    avestd = useful['PtsODev'].mean()

    for i, row in useful.iterrows():
        opp = row['Opp']
        rand1 = np.random.uniform(-1, 1, n_simulations)
        rand2 = np.random.uniform(-1, 1, n_simulations)
        rand3 = np.random.uniform(-1, 1, n_simulations)

        if opp == 'BYE':
            defense = np.zeros(n_simulations)
            points_for = np.zeros(n_simulations)

        else:
            defense = opp_stats[opp]['PtsO'] + opp_stats[opp]['PtsODev']*rand1
            defense_deviation = ave + avestd * rand2
            defense_over_average = defense - defense_deviation
            offense = row['Pts'] + row['PtsDev'] * rand3
            homefield_adv = 2.5 #detemine team specific homefield advantage later
            if row['Team'] in homefield["Team"].values:
                points_for = offense + homefield_adv + defense_over_average 
            else:
                points_for = offense + defense_over_average


        Points_For.append(points_for.mean().round())

    FinalScores['Points For'] = Points_For


    HomeScores = FinalScores[FinalScores["Team"].isin(homefield["Team"])]
    AwayScores = FinalScores[~FinalScores["Team"].isin(homefield["Team"])]
    FinalScores = HomeScores

    points_map = AwayScores.set_index("Team")["Points For"]
    FinalScores["Points Against"] = FinalScores["Opp"].map(points_map)

    FinalScores['Total'] = pd.to_numeric(FinalScores['Points For']) + pd.to_numeric(FinalScores['Points Against'])
    FinalScores['Home Spread'] = -pd.to_numeric(FinalScores['Points For']) + pd.to_numeric(FinalScores['Points Against'])



    FinalScores['Winner'] = np.where(FinalScores['Points For'] > FinalScores['Points Against'], FinalScores['Team'], np.where(FinalScores['Points For'] < FinalScores['Points Against'], FinalScores['Opp'], FinalScores['Team']))    
    
    FinalScores = FinalScores.rename(columns={"Team": "Home"})
    FinalScores = FinalScores.rename(columns={"Opp": "Away"})
    FinalScores = FinalScores.rename(columns={"Points For": "Home Score"})
    FinalScores = FinalScores.rename(columns={"Points Against": "Away Score"})

    FinalScores['Rank'] = range(1, len(FinalScores) + 1)

    cols = ['Rank'] + [col for col in FinalScores.columns if col != 'Rank']
    FinalScores = FinalScores[cols]

    return FinalScores


def teampredictionshtml(finalscores, week):
    html_string = finalscores.to_html(classes='display', index=False).replace('class="dataframe display"', 'class="display"')

        # Full HTML file with sorting and ALL rows shown
    html_script = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title> Game Predictions </title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="icon" type="image/png" sizes="96x96" href="/WebProjects/images/favicon-96x96.png" />
        <link rel="icon" type="image/svg+xml" href="/WebProjects/images/favicon.svg" />
        <link rel="shortcut icon" href="/WebProjects/images/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/WebProjects/images/apple-touch-icon.png" />
        <meta name="apple-mobile-web-app-title" content="MyWebSit" />
        <link rel="manifest" href="/WebProjects/images/site.webmanifest" />

        <link rel="stylesheet" href="/WebProjects/style.css">


        </head>
        <body>

        <div class="topnav">
        <a href="/WebProjects/index.html">Home</a>
            <div class="dropdown">
            <button class="dropbtn active">Football
                <i class="fa fa-caret-down"></i>
            </button>
            <div class="dropdown-content">
                <a href="/WebProjects/WeeklyPred_html/SuperFlex.html">Weekly Predictions</a>
                <a href="/WebProjects/ROS_html/Rest Of Season.html">Rest of Season Predictions</a>
                <a href="/WebProjects/WeeklyScores_html/Weekly Game Predictions.html">Weekly Game Predictions</a>
                <a href="/WebProjects/Dominance_html/QBDom.html">Offensive Focus</a>
            </div>
            </div>
        <a href="/WebProjects/PreseasonMLBPredictions.html">MLB Preseason Predictions
        <a href="/WebProjects/Fitness_html/fitness.html">Fitness</a>
        <a href="/WebProjects/about.html">About</a>
        </div>
        

        <img src="/WebProjects/images/Banner_Logo.png" alt="Header Image" class="header-img">

        <h1>Week {week} Predictions</h1>

        <div class="topnav">
        <input type="text" id="searchBar" placeholder="Search...">
        </div>






        {html_string}

        <script>
        function getCellValue(row, index) {{
            return row.cells[index].textContent.trim();
        }}

        function comparer(index, asc) {{
            return function(a, b) {{
            const v1 = getCellValue(a, index);
            const v2 = getCellValue(b, index);

            const num1 = parseFloat(v1);
            const num2 = parseFloat(v2);
            const bothNumbers = !isNaN(num1) && !isNaN(num2);

            if (bothNumbers) {{
                return asc ? num1 - num2 : num2 - num1;
            }} else {{
                return asc ? v1.localeCompare(v2) : v2.localeCompare(v1);
            }}
            }};
        }}

        document.addEventListener("DOMContentLoaded", function () {{
            document.querySelectorAll("th").forEach(function (th, index) {{
            let ascending = true;
            if (index === 0) return;
            th.addEventListener("click", function () {{
                const table = th.closest("table");
                const tbody = table.querySelector("tbody");
                const rows = Array.from(tbody.querySelectorAll("tr"));
                rows.sort(comparer(index, ascending));
                //rows.forEach(row => tbody.appendChild(row));
                rows.forEach((row, i) => {{
                    row.cells[0].textContent = i + 1; // Reset Rank to match new row position
                    tbody.appendChild(row);
                }});
                ascending = !ascending;
            }});
            }});
        }});
        </script>

        

        <script>
        const searchBar = document.getElementById('searchBar');
        const table = document.querySelector('table');
        const rows = table.getElementsByTagName('tr');

        searchBar.addEventListener('keyup', function () {{
            const searchText = searchBar.value.toLowerCase();

            for (let i = 1; i < rows.length; i++) {{
            const row = rows[i];
            const rowText = row.textContent.toLowerCase();
            row.style.display = rowText.includes(searchText) ? '' : 'none';
            }}
        }});
        </script>

        

        </body>
        </html>
        """

    # Save to HTML file
    with open(f"WeeklyScores_html/Weekly Game Predictions.html", "w", encoding="utf-8") as f:
        f.write(html_script)


def analysis(useful, individualtotals):
    #Separate by position

    QBstatcolumns = ['Player', 'Team', 'Off Focus', 'YPA', 'TD:Int', 'TotalTD%']
    statcolumns = ['Player', 'Team', 'Off Focus', 'Tgt%', 'RecYds%', 'RecTD%', 'Rush%', 'RushYds%', 'RushTD%', 'TotalTD%']


    QBDom = pd.DataFrame(columns=QBstatcolumns)
    FlexDom = pd.DataFrame(columns=statcolumns)
    WRDom = pd.DataFrame(columns=statcolumns)
    RBDom = pd.DataFrame(columns=statcolumns)
    TEDom = pd.DataFrame(columns=statcolumns)


    #Populate each DF with Player names, Team name, Position
    for i, row in useful.iterrows():
        keywords = ['QB']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            QBDom.at[i, 'Player'] = row['Player']
            QBDom.at[i, 'Team'] = row['Team']

    for i, row in useful.iterrows():
        keywords = ['WR', 'RB', 'TE']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            FlexDom.at[i, 'Player'] = row['Player']
            FlexDom.at[i, 'Team'] = row['Team']

    for i, row in useful.iterrows():
        keywords = ['WR']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            WRDom.at[i, 'Player'] = row['Player']
            WRDom.at[i, 'Team'] = row['Team']

    for i, row in useful.iterrows():
        keywords = ['RB']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            RBDom.at[i, 'Player'] = row['Player']
            RBDom.at[i, 'Team'] = row['Team']

    for i, row in useful.iterrows():
        keywords = ['TE']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            TEDom.at[i, 'Player'] = row['Player']
            TEDom.at[i, 'Team'] = row['Team']
    

    for i, row in QBDom.iterrows():
        key = row['Player']
       

        usefulrow = useful[useful['Player'] == key].iloc[0]
        teamtotalrow = individualtotals[individualtotals['Player'] == key].iloc[0]
       

        passatt = usefulrow['PassAtt']
        passyds = usefulrow['PassYds']
        passtds = usefulrow['PassTD']
        passints = usefulrow['Int'] 
        totalpasstds = teamtotalrow['TeamTotalPassTD']
        totalrectds = teamtotalrow['TeamTotalRecTD']
        totalrushtds = teamtotalrow['TeamTotalRushTD']
        

        if passatt != 0:
            QBDom.at[i, 'YPA'] = round(passyds/passatt,1)
        else:
            QBDom.at[i, 'YPA'] = 0
        
        if passints != 0:
            QBDom.at[i, 'TD:Int'] = round(passtds/passints,1)
        else:
            QBDom.at[i, 'TD:Int'] = 0
        
        if totalpasstds + totalrectds + totalrushtds != 0:
            QBDom.at[i, 'TotalTD%'] = round(passtds/(totalpasstds + totalrectds + totalrushtds) * 100,1)
        else:
            QBDom.at[i, 'TotalTD%'] = 0
        
        if passatt != 0 and passints != 0 and totalpasstds + totalrectds + totalrushtds != 0:
            QBDom.at[i, 'Off Focus'] = round(passyds/passatt + passtds/passints + totalpasstds/(totalpasstds + totalrectds + totalrushtds),1)
        else:
            QBDom.at[i, 'Off Focus'] = 0


    for i, row in FlexDom.iterrows():
        key = row['Player']
       

        usefulrow = useful[useful['Player'] == key].iloc[0]
        teamtotalrow = individualtotals[individualtotals['Player'] == key].iloc[0]
       

        targets = usefulrow['Tgt']
        totaltargets = teamtotalrow['TeamTotalTgt'] 
        recyds = usefulrow['RecYds']
        totalrecyds = teamtotalrow['TeamTotalRecYds']
        rectds = usefulrow['RecTD']
        rushatt = usefulrow['RushAtt']
        totalrushatt = teamtotalrow['TeamTotalRushAtt']
        rushyds = usefulrow['RushYds']
        totalrushyds = teamtotalrow['TeamTotalRushYds']
        rushtds = usefulrow['RushTD']
        totalpasstds = teamtotalrow['TeamTotalPassTD']
        totalrectds = teamtotalrow['TeamTotalRecTD']
        totalrushtds = teamtotalrow['TeamTotalRushTD']


        if totaltargets != 0:
            FlexDom.at[i, 'Tgt%'] = round(targets/totaltargets * 100,1)
        else:
            FlexDom.at[i, 'Tgt%'] = 0
        
        if totalrecyds !=0:
            FlexDom.at[i, 'RecYds%'] = round(recyds/totalrecyds * 100,1)
        else:
            FlexDom.at[i, 'RecYds%'] = 0
        
        if totalrectds != 0:
            FlexDom.at[i, 'RecTD%'] = round(rectds/totalrectds * 100,1)
        else:
            FlexDom.at[i, 'RecTD%'] = 0

        if totalrushatt != 0:
            FlexDom.at[i, 'Rush%'] = round(rushatt/totalrushatt * 100,1)
        else:
            FlexDom.at[i, 'Rush%'] = 0

        if totalrushyds != 0:
            FlexDom.at[i, 'RushYds%'] = round(rushyds/totalrushyds * 100,1)
        else:
            FlexDom.at[i, 'RushYds%'] = 0
        
        if totalrushtds != 0:
            FlexDom.at[i, 'RushTD%'] = round(rushtds/totalrushtds * 100,1)
        else:
            FlexDom.at[i, 'RushTD%'] = 0
        
        if totalpasstds + totalrectds + totalrushtds != 0:
            FlexDom.at[i, 'TotalTD%'] = round(rectds/(totalpasstds + totalrectds + totalrushtds) * 100,1)
        else:
            FlexDom.at[i, 'TotalTD%'] = 0
        
        if totalrushtds != 0 and totalrushyds != 0 and totalrushatt != 0 and totaltargets != 0 and totalrecyds !=0 and totalrectds != 0 and totalpasstds + totalrectds + totalrushtds != 0:
            FlexDom.at[i, 'Off Focus'] = round((rushtds/totalrushtds + rushyds/totalrushyds + rushatt/totalrushatt + targets/totaltargets + recyds/totalrecyds + rectds/totalrectds + rectds/(totalpasstds + totalrectds + totalrushtds)) * 100,1)
        else:
            FlexDom.at[i, 'Off Focus'] = 0



    for i, row in WRDom.iterrows():
        key = row['Player']
       

        usefulrow = useful[useful['Player'] == key].iloc[0]
        teamtotalrow = individualtotals[individualtotals['Player'] == key].iloc[0]
       

        targets = usefulrow['Tgt']
        totaltargets = teamtotalrow['TeamTotalTgt'] 
        recyds = usefulrow['RecYds']
        totalrecyds = teamtotalrow['TeamTotalRecYds']
        rectds = usefulrow['RecTD']
        rushatt = usefulrow['RushAtt']
        totalrushatt = teamtotalrow['TeamTotalRushAtt']
        rushyds = usefulrow['RushYds']
        totalrushyds = teamtotalrow['TeamTotalRushYds']
        rushtds = usefulrow['RushTD']
        totalpasstds = teamtotalrow['TeamTotalPassTD']
        totalrectds = teamtotalrow['TeamTotalRecTD']
        totalrushtds = teamtotalrow['TeamTotalRushTD']


        if totaltargets != 0:
            WRDom.at[i, 'Tgt%'] = round(targets/totaltargets * 100,1)
        else:
            WRDom.at[i, 'Tgt%'] = 0
        
        if totalrecyds !=0:
            WRDom.at[i, 'RecYds%'] = round(recyds/totalrecyds * 100,1)
        else:
            WRDom.at[i, 'RecYds%'] = 0
        
        if totalrectds != 0:
            WRDom.at[i, 'RecTD%'] = round(rectds/totalrectds * 100,1)
        else:
            WRDom.at[i, 'RecTD%'] = 0

        if totalrushatt != 0:
            WRDom.at[i, 'Rush%'] = round(rushatt/totalrushatt * 100,1)
        else:
            WRDom.at[i, 'Rush%'] = 0

        if totalrushyds != 0:
            WRDom.at[i, 'RushYds%'] = round(rushyds/totalrushyds * 100,1)
        else:
            WRDom.at[i, 'RushYds%'] = 0
        
        if totalrushtds != 0:
            WRDom.at[i, 'RushTD%'] = round(rushtds/totalrushtds * 100,1)
        else:
            WRDom.at[i, 'RushTD%'] = 0
        
        if totalpasstds + totalrectds + totalrushtds != 0:
            WRDom.at[i, 'TotalTD%'] = round(rectds/(totalpasstds + totalrectds + totalrushtds) * 100,1)
        else:
            WRDom.at[i, 'TotalTD%'] = 0
        
        if totalrushtds != 0 and totalrushyds != 0 and totalrushatt != 0 and totaltargets != 0 and totalrecyds !=0 and totalrectds != 0 and totalpasstds + totalrectds + totalrushtds != 0:
            WRDom.at[i, 'Off Focus'] = round((rushtds/totalrushtds + rushyds/totalrushyds + rushatt/totalrushatt + targets/totaltargets + recyds/totalrecyds + rectds/totalrectds + rectds/(totalpasstds + totalrectds + totalrushtds)) * 100,1)
        else:
            WRDom.at[i, 'Off Focus'] = 0


    for i, row in RBDom.iterrows():
        key = row['Player']
       

        usefulrow = useful[useful['Player'] == key].iloc[0]
        teamtotalrow = individualtotals[individualtotals['Player'] == key].iloc[0]
       
        targets = usefulrow['Tgt']
        totaltargets = teamtotalrow['TeamTotalTgt'] 
        recyds = usefulrow['RecYds']
        totalrecyds = teamtotalrow['TeamTotalRecYds']
        rectds = usefulrow['RecTD']
        rushatt = usefulrow['RushAtt']
        totalrushatt = teamtotalrow['TeamTotalRushAtt']
        rushyds = usefulrow['RushYds']
        totalrushyds = teamtotalrow['TeamTotalRushYds']
        rushtds = usefulrow['RushTD']
        totalpasstds = teamtotalrow['TeamTotalPassTD']
        totalrectds = teamtotalrow['TeamTotalRecTD']
        totalrushtds = teamtotalrow['TeamTotalRushTD']
        
        if totaltargets != 0:
            RBDom.at[i, 'Tgt%'] = round(targets/totaltargets * 100,1)
        else:
            RBDom.at[i, 'Tgt%'] = 0
        
        if totalrecyds !=0:
            RBDom.at[i, 'RecYds%'] = round(recyds/totalrecyds * 100,1)
        else:
            RBDom.at[i, 'RecYds%'] = 0
        
        if totalrectds != 0:
            RBDom.at[i, 'RecTD%'] = round(rectds/totalrectds * 100,1)
        else:
            RBDom.at[i, 'RecTD%'] = 0

        if totalrushatt != 0:
            RBDom.at[i, 'Rush%'] = round(rushatt/totalrushatt * 100,1)
        else:
            RBDom.at[i, 'Rush%'] = 0

        if totalrushyds != 0:
            RBDom.at[i, 'RushYds%'] = round(rushyds/totalrushyds * 100,1)
        else:
            RBDom.at[i, 'RushYds%'] = 0
        
        if totalrushtds != 0:
            RBDom.at[i, 'RushTD%'] = round(rushtds/totalrushtds * 100,1)
        else:
            RBDom.at[i, 'RushTD%'] = 0
        
        if totalpasstds + totalrectds + totalrushtds != 0:
            RBDom.at[i, 'TotalTD%'] = round(rushtds/(totalpasstds + totalrectds + totalrushtds) * 100,1)
        else:
            RBDom.at[i, 'TotalTD%'] = 0
        
        if totalrushtds != 0 and totalrushyds != 0 and totalrushatt != 0 and totaltargets != 0 and totalrecyds !=0 and totalrectds != 0 and totalpasstds + totalrectds + totalrushtds != 0:
            RBDom.at[i, 'Off Focus'] = round((rushtds/totalrushtds + rushyds/totalrushyds + rushatt/totalrushatt + targets/totaltargets + recyds/totalrecyds + rectds/totalrectds + rectds/(totalpasstds + totalrectds + totalrushtds)) * 100,1)
        else:
            RBDom.at[i, 'Off Focus'] = 0

    for i, row in TEDom.iterrows():
        key = row['Player']
       

        usefulrow = useful[useful['Player'] == key].iloc[0]
        teamtotalrow = individualtotals[individualtotals['Player'] == key].iloc[0]
       

        targets = usefulrow['Tgt']
        totaltargets = teamtotalrow['TeamTotalTgt'] 
        recyds = usefulrow['RecYds']
        totalrecyds = teamtotalrow['TeamTotalRecYds']
        rectds = usefulrow['RecTD']
        rushatt = usefulrow['RushAtt']
        totalrushatt = teamtotalrow['TeamTotalRushAtt']
        rushyds = usefulrow['RushYds']
        totalrushyds = teamtotalrow['TeamTotalRushYds']
        rushtds = usefulrow['RushTD']
        totalpasstds = teamtotalrow['TeamTotalPassTD']
        totalrectds = teamtotalrow['TeamTotalRecTD']
        totalrushtds = teamtotalrow['TeamTotalRushTD']

        
        if totaltargets != 0:
            TEDom.at[i, 'Tgt%'] = round(targets/totaltargets * 100,1)
        else:
            TEDom.at[i, 'Tgt%'] = 0
        
        if totalrecyds !=0:
            TEDom.at[i, 'RecYds%'] = round(recyds/totalrecyds * 100,1)
        else:
            TEDom.at[i, 'RecYds%'] = 0
        
        if totalrectds != 0:
            TEDom.at[i, 'RecTD%'] = round(rectds/totalrectds * 100,1)
        else:
            TEDom.at[i, 'RecTD%'] = 0

        if totalrushatt != 0:
            TEDom.at[i, 'Rush%'] = round(rushatt/totalrushatt * 100,1)
        else:
            TEDom.at[i, 'Rush%'] = 0

        if totalrushyds != 0:
            TEDom.at[i, 'RushYds%'] = round(rushyds/totalrushyds * 100,1)
        else:
            TEDom.at[i, 'RushYds%'] = 0
        
        if totalrushtds != 0:
            TEDom.at[i, 'RushTD%'] = round(rushtds/totalrushtds * 100,1)
        else:
            TEDom.at[i, 'RushTD%'] = 0
        
        if totalpasstds + totalrectds + totalrushtds != 0:
            TEDom.at[i, 'TotalTD%'] = round(rectds/(totalpasstds + totalrectds + totalrushtds) * 100,1)
        else:
            TEDom.at[i, 'TotalTD%'] = 0
        
        if totalrushtds != 0 and totalrushyds != 0 and totalrushatt != 0 and totaltargets != 0 and totalrecyds !=0 and totalrectds != 0 and totalpasstds + totalrectds + totalrushtds != 0:
            TEDom.at[i, 'Off Focus'] = round((rushtds/totalrushtds + rushyds/totalrushyds + rushatt/totalrushatt + targets/totaltargets + recyds/totalrecyds + rectds/totalrectds + rectds/(totalpasstds + totalrectds + totalrushtds)) * 100,1)
        else:
            TEDom.at[i, 'Off Focus'] = 0


    QBDom['Rank'] = range(1, len(QBDom) + 1)
    FlexDom['Rank'] = range(1, len(FlexDom) + 1)
    WRDom['Rank'] = range(1, len(WRDom) + 1)
    RBDom['Rank'] = range(1, len(RBDom) + 1)
    TEDom['Rank'] = range(1, len(TEDom) + 1)

    cols = ['Rank'] + [col for col in QBDom.columns if col != 'Rank']
    QBDom = QBDom[cols]

    cols = ['Rank'] + [col for col in FlexDom.columns if col != 'Rank']
    FlexDom = FlexDom[cols]

    cols = ['Rank'] + [col for col in WRDom.columns if col != 'Rank']
    WRDom = WRDom[cols]

    cols = ['Rank'] + [col for col in RBDom.columns if col != 'Rank']
    RBDom = RBDom[cols]

    cols = ['Rank'] + [col for col in TEDom.columns if col != 'Rank']
    TEDom = TEDom[cols]

    

    Dom_DataFrames = {'QBDom': QBDom, 'FlexDom': FlexDom, 'WRDom': WRDom, 'RBDom': RBDom, 'TEDom': TEDom}

    return Dom_DataFrames


def dominancehtml(alldataframes):
    #html_dict = {}

    for name, df in alldataframes.items():

        html_string = df.to_html(classes='display', index=False).replace('class="dataframe display"', 'class="display"')

        # Full HTML file with sorting and ALL rows shown
        html_script = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>{name} Stats</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="icon" type="image/png" sizes="96x96" href="/WebProjects/images/favicon-96x96.png" />
        <link rel="icon" type="image/svg+xml" href="/WebProjects/images/favicon.svg" />
        <link rel="shortcut icon" href="/WebProjects/images/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/WebProjects/images/apple-touch-icon.png" />
        <meta name="apple-mobile-web-app-title" content="MyWebSit" />
        <link rel="manifest" href="/WebProjects/images/site.webmanifest" />

        <link rel="stylesheet" href="/WebProjects/style.css">


        </head>
        <body>

        <div class="topnav">
        <a href="/WebProjects/index.html">Home</a>
            <div class="dropdown">
            <button class="dropbtn active">Football
                <i class="fa fa-caret-down"></i>
            </button>
            <div class="dropdown-content">
                <a href="/WebProjects/WeeklyPred_html/SuperFlex.html">Weekly Predictions</a>
                <a href="/WebProjects/ROS_html/Rest Of Season.html">Rest of Season Predictions</a>
                <a href="/WebProjects/WeeklyScores_html/Weekly Game Predictions.html">Weekly Game Predictions</a>
                <a href="/WebProjects/Dominance_html/QBDom.html">Offensive Focus</a>
            </div>
            </div>
            <div class="dropdown">
            <button class="dropbtn">Baseball
                <i class="fa fa-caret-down"></i>
            </button>
            <div class="dropdown-content">
                <a href="/WebProjects/PreseasonMLBHittingPredictions.html">MLB Preseason Hitting Predictions</a>
                <a href="/WebProjects/PreseasonMLBPitchingPredictions.html">MLB Preseason Pitching Predictions</a>
            </div>
            </div>        
        <a href="/WebProjects/Fitness_html/fitness.html">Fitness</a>
        <a href="/WebProjects/about.html">About</a>
        </div>
        

        <img src="/WebProjects/images/Banner_Logo.png" alt="Header Image" class="header-img">

        <h1>Offensive Focus</h1>

        <div class="topnav">
        <input type="text" id="searchBar" placeholder="Search...">
        </div>

        <div class="topnav">
        <a {"class='active'" if name == "QBDom" else ""} href="QBDom.html">QB</a>
        <a {"class='active'" if name == "FlexDom" else ""} href="FlexDom.html">Flex</a>
        <a {"class='active'" if name == "WRDom" else ""} href="WRDom.html">WR</a>
        <a {"class='active'" if name == "RBDom" else ""} href="RBDom.html">RB</a>
        <a {"class='active'" if name == "TEDom" else ""} href="TEDom.html">TE</a>

        </div>





        {html_string}

        <script>
        function getCellValue(row, index) {{
            return row.cells[index].textContent.trim();
        }}

        function comparer(index, asc) {{
            return function(a, b) {{
            const v1 = getCellValue(a, index);
            const v2 = getCellValue(b, index);

            const num1 = parseFloat(v1);
            const num2 = parseFloat(v2);
            const bothNumbers = !isNaN(num1) && !isNaN(num2);

            if (bothNumbers) {{
                return asc ? num1 - num2 : num2 - num1;
            }} else {{
                return asc ? v1.localeCompare(v2) : v2.localeCompare(v1);
            }}
            }};
        }}

        document.addEventListener("DOMContentLoaded", function () {{
            document.querySelectorAll("th").forEach(function (th, index) {{
            let ascending = true;
            if (index === 0) return;
            th.addEventListener("click", function () {{
                const table = th.closest("table");
                const tbody = table.querySelector("tbody");
                const rows = Array.from(tbody.querySelectorAll("tr"));
                rows.sort(comparer(index, ascending));
                //rows.forEach(row => tbody.appendChild(row));
                rows.forEach((row, i) => {{
                    row.cells[0].textContent = i + 1; // Reset Rank to match new row position
                    tbody.appendChild(row);
                }});
                ascending = !ascending;
            }});
            }});
        }});
        </script>

        

        <script>
        const searchBar = document.getElementById('searchBar');
        const table = document.querySelector('table');
        const rows = table.getElementsByTagName('tr');

        searchBar.addEventListener('keyup', function () {{
            const searchText = searchBar.value.toLowerCase();

            for (let i = 1; i < rows.length; i++) {{
            const row = rows[i];
            const rowText = row.textContent.toLowerCase();
            row.style.display = rowText.includes(searchText) ? '' : 'none';
            }}
        }});
        </script>

        

        </body>
        </html>
        """

        # Save to HTML file
        with open(f"Dominance_html/{name}.html", "w", encoding="utf-8") as f:
            f.write(html_script)


#MLB Scripts

def hitterpredictions(csv1, csv2, csv3, csv4):

    if not isinstance(csv1, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv1)}: {csv1}")
    if not csv1.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv1}")
    if not os.path.exists(csv1):
        raise ValueError(f"File not found: {csv1}")

    if not isinstance(csv2, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv2)}: {csv2}")
    if not csv2.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv2}")
    if not os.path.exists(csv2):
        raise ValueError(f"File not found: {csv2}")

    if not isinstance(csv3, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv3)}: {csv3}")
    if not csv3.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv3}")
    if not os.path.exists(csv3):
        raise ValueError(f"File not found: {csv3}")

    if not isinstance(csv4, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv4)}: {csv4}")
    if not csv4.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv4}")
    if not os.path.exists(csv4):
        raise ValueError(f"File not found: {csv4}")

    df1 = pd.read_csv(csv1)
    df1["Player"] = df1["Player"].str.replace(r"[\*#]+$", "", regex=True).str.strip()
    df1['Player'] = df1['Player'].apply(lambda x: "".join(c for c in unicodedata.normalize("NFKC", str(x)) if c not in "*#\u200B\u200C\u200D\uFEFF"))
    df2 = pd.read_csv(csv2)
    df2["Player"] = df2["Player"].str.replace(r"[\*#]+$", "", regex=True).str.strip()
    df2['Player'] = df2['Player'].apply(lambda x: "".join(c for c in unicodedata.normalize("NFKC", str(x)) if c not in "*#\u200B\u200C\u200D\uFEFF"))
    df3 = pd.read_csv(csv3)
    df3["Player"] = df3["Player"].str.replace(r"[\*#]+$", "", regex=True).str.strip()
    df3['Player'] = df3['Player'].apply(lambda x: "".join(c for c in unicodedata.normalize("NFKC", str(x)) if c not in "*#\u200B\u200C\u200D\uFEFF"))
    df4 = pd.read_csv(csv4)
    df4["Name"] = df4["Name"].str.replace(r"[\*#]+$", "", regex=True).str.strip()
    df4['Name'] = df4['Name'].apply(lambda x: "".join(c for c in unicodedata.normalize("NFKC", str(x)) if c not in "*#\u200B\u200C\u200D\uFEFF"))

    #row1 = df1[df1['Player'] == 'CJ Abrams']
    #row2 = df2[df2['Player'] == 'CJ Abrams']
    #row3 = df3[df3['Player'] == 'CJ Abrams']
    #row4 = df4[df4['Name'] == 'CJ Abrams']

    #print(row1)
    #print(row2)
    #print(row3)
    #print(row4)

    future = pd.DataFrame(columns=df3.columns)
    future['Player'] = df4['Name']
    future['Age'] = df4['Age']
    future['Team'] = df4['Tm']
    future['Pos'] = df4['Pos Summary']
    future = future.drop('Rk', axis=1) 
    future = future.drop('Lg', axis=1) 
    future = future.drop('WAR', axis=1) 
    future = future.drop('Awards', axis=1) 
    future = future.drop('Player-additional', axis=1) 


    future['Player'] = future['Player'].astype(str)
    df1['Player'] = df1['Player'].astype(str)
    df2['Player'] = df2['Player'].astype(str)
    df3['Player'] = df3['Player'].astype(str)

    future['PlayerID'] = future['Player'] + "_" + future['Team']
    df1['PlayerID'] = df1['Player'] + "_" + df1['Team']
    df2['PlayerID'] = df2['Player'] + "_" + df2['Team']
    df3['PlayerID'] = df2['Player'] + "_" + df3['Team']

    future['PlayerID'] = future['PlayerID'].astype(str)
    df1['PlayerID'] = df1['PlayerID'].astype(str)
    df2['PlayerID'] = df2['PlayerID'].astype(str)
    df3['PlayerID'] = df3['PlayerID'].astype(str)


    def gaussian_pdf(age):
        return np.exp(-0.5 * ((age - 28)/5)**2)

    cols = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'SO', 'OPS+', 'Rbat+', 'TB', 'GIDP', 'HBP', 'SH', 'SF', 'IBB']

    # Merge future with df1, df2, df3
    merged_df = future.copy()

    # List of dataframes to merge with suffixes
    dfs = [(df1, '_df1'), (df2, '_df2'), (df3, '_df3')]

    # Merge each dataframe
    for df, suffix in dfs:
        merged_df = pd.merge(merged_df, df, on='Player', how='left', suffixes=('', suffix))

    # Rename the columns for the specified ones
    for col in cols:
        for suffix in ['_df1', '_df2', '_df3']:
            if f'{col}{suffix}' in merged_df.columns:
                merged_df.rename(columns={f'{col}{suffix}': f'{col}{suffix}'}, inplace=True)

    # Now `merged_df` has all the columns merged and renamed appropriately


    #future['is_in_df3'] = future['Player'].isin(df3['Player'])
    #future['is_in_df2'] = future['Player'].isin(df2['Player'])
    #future['is_in_df1'] = future['Player'].isin(df1['Player'])

    num_sim = 1000

    weights = [np.random.uniform(0.6, 0.8, num_sim), np.random.uniform(0.4, 0.5, num_sim), np.random.uniform(0,0.2, num_sim)]
    weights2 = [np.random.uniform(0.7, 0.9, num_sim), np.random.uniform(0.1, 0.3, num_sim)]
    weights1 = [np.random.uniform(0.9, 1.1, num_sim)]

    predictedgames = []
    predictedPA = []
    predictedAB = []
    predictedR = []
    predictedH = []
    predictedDub = []
    predictedTrip = []
    predictedHR = []
    predictedRBI = []
    predictedSB = []
    predictedCS = []
    predictedBB = []
    predictedSO = []
    predictedOPSplus = []
    predictedRbat = []
    predictedTB = []
    predictedGIDP = []
    predictedHBP = []
    predictedSH = []
    predictedSF = []
    predictedIBB = []


    #duplicates = merged_df['PlayerID'][merged_df['PlayerID'].duplicated(keep=False)]
    #print(duplicates)
    #merged_df = merged_df.fillna(0)
    merged_df[merged_df.select_dtypes('number').columns] = merged_df.select_dtypes('number').fillna(0)
    merged_df = merged_df.drop_duplicates(subset='PlayerID')
    merged_df = merged_df.reset_index(drop=True)

    #print(merged_df.head(5))

    for i, row in merged_df.iterrows():
        player = row['Player']  # Get the player name

        in_df1 = df1['Player'].isin([player]).any()
        in_df2 = df2['Player'].isin([player]).any()
        in_df3 = df3['Player'].isin([player]).any()


        if in_df1 and in_df2 and in_df3:
            games = gaussian_pdf(row['Age']) * (weights[0]*row['G_df3'] + weights[1]*row['G_df2'] + weights[2]*row['G_df1'])
            PA = gaussian_pdf(row['Age']) * (weights[0]*row['PA_df3'] + weights[1]*row['PA_df2'] + weights[2]*row['PA_df1'])
            AB = gaussian_pdf(row['Age']) * (weights[0]*row['AB_df3'] + weights[1]*row['AB_df2'] + weights[2]*row['AB_df1'])
            R = gaussian_pdf(row['Age']) * (weights[0]*row['R_df3'] + weights[1]*row['R_df2'] + weights[2]*row['R_df1'])
            H = gaussian_pdf(row['Age']) * (weights[0]*row['H_df3'] + weights[1]*row['H_df2'] + weights[2]*row['H_df1'])
            Dub = gaussian_pdf(row['Age']) * (weights[0]*row['2B_df3'] + weights[1]*row['2B_df2'] + weights[2]*row['2B_df1'])
            Trip = gaussian_pdf(row['Age']) * (weights[0]*row['3B_df3'] + weights[1]*row['3B_df2'] + weights[2]*row['3B_df1'])
            HR = gaussian_pdf(row['Age']) * (weights[0]*row['HR_df3'] + weights[1]*row['HR_df2'] + weights[2]*row['HR_df1'])
            RBI = gaussian_pdf(row['Age']) * (weights[0]*row['RBI_df3'] + weights[1]*row['RBI_df2'] + weights[2]*row['RBI_df1'])
            SB = gaussian_pdf(row['Age']) * (weights[0]*row['SB_df3'] + weights[1]*row['SB_df2'] + weights[2]*row['SB_df1'])
            CS = gaussian_pdf(row['Age']) * (weights[0]*row['CS_df3'] + weights[1]*row['CS_df2'] + weights[2]*row['CS_df1'])
            BB = gaussian_pdf(row['Age']) * (weights[0]*row['BB_df3'] + weights[1]*row['BB_df2'] + weights[2]*row['BB_df1'])
            SO = gaussian_pdf(row['Age']) * (weights[0]*row['SO_df3'] + weights[1]*row['SO_df2'] + weights[2]*row['SO_df1'])
            OPSplus = gaussian_pdf(row['Age']) * (weights[0]*row['OPS+_df3'] + weights[1]*row['OPS+_df2'] + weights[2]*row['OPS+_df1'])
            Rbat = gaussian_pdf(row['Age']) * (weights[0]*row['Rbat+_df3'] + weights[1]*row['Rbat+_df2'] + weights[2]*row['Rbat+_df1'])
            TB = gaussian_pdf(row['Age']) * (weights[0]*row['TB_df3'] + weights[1]*row['TB_df2'] + weights[2]*row['TB_df1'])
            GIDP = gaussian_pdf(row['Age']) * (weights[0]*row['GIDP_df3'] + weights[1]*row['GIDP_df2'] + weights[2]*row['GIDP_df1'])
            HBP = gaussian_pdf(row['Age']) * (weights[0]*row['HBP_df3'] + weights[1]*row['HBP_df2'] + weights[2]*row['HBP_df1'])
            SH = gaussian_pdf(row['Age']) * (weights[0]*row['SH_df3'] + weights[1]*row['SH_df2'] + weights[2]*row['SH_df1'])
            SF = gaussian_pdf(row['Age']) * (weights[0]*row['SF_df3'] + weights[1]*row['SF_df2'] + weights[2]*row['SF_df1'])
            IBB = gaussian_pdf(row['Age']) * (weights[0]*row['IBB_df3'] + weights[1]*row['IBB_df2'] + weights[2]*row['IBB_df1'])
        elif in_df3 and in_df2:
            games = gaussian_pdf(row['Age']) * (weights2[0]*row['G_df3'] + weights2[1]*row['G_df2'])
            PA = gaussian_pdf(row['Age']) * (weights2[0]*row['PA_df3'] + weights2[1]*row['PA_df2'])
            AB = gaussian_pdf(row['Age']) * (weights2[0]*row['AB_df3'] + weights2[1]*row['AB_df2'])
            R = gaussian_pdf(row['Age']) * (weights2[0]*row['R_df3'] + weights2[1]*row['R_df2'])
            H = gaussian_pdf(row['Age']) * (weights2[0]*row['H_df3'] + weights2[1]*row['H_df2'])
            Dub = gaussian_pdf(row['Age']) * (weights2[0]*row['2B_df3'] + weights2[1]*row['2B_df2'])
            Trip = gaussian_pdf(row['Age']) * (weights2[0]*row['3B_df3'] + weights2[1]*row['3B_df2'])
            HR = gaussian_pdf(row['Age']) * (weights2[0]*row['HR_df3'] + weights2[1]*row['HR_df2'])
            RBI = gaussian_pdf(row['Age']) * (weights2[0]*row['RBI_df3'] + weights2[1]*row['RBI_df2'])
            SB = gaussian_pdf(row['Age']) * (weights2[0]*row['SB_df3'] + weights2[1]*row['SB_df2'])
            CS = gaussian_pdf(row['Age']) * (weights2[0]*row['CS_df3'] + weights2[1]*row['CS_df2'])
            BB = gaussian_pdf(row['Age']) * (weights2[0]*row['BB_df3'] + weights2[1]*row['BB_df2'])
            SO = gaussian_pdf(row['Age']) * (weights2[0]*row['SO_df3'] + weights2[1]*row['SO_df2'])
            OPSplus = gaussian_pdf(row['Age']) * (weights2[0]*row['OPS+_df3'] + weights2[1]*row['OPS+_df2'])
            Rbat = gaussian_pdf(row['Age']) * (weights2[0]*row['Rbat+_df3'] + weights2[1]*row['Rbat+_df2'])
            TB = gaussian_pdf(row['Age']) * (weights2[0]*row['TB_df3'] + weights2[1]*row['TB_df2'])
            GIDP = gaussian_pdf(row['Age']) * (weights2[0]*row['GIDP_df3'] + weights2[1]*row['GIDP_df2'])
            HBP = gaussian_pdf(row['Age']) * (weights2[0]*row['HBP_df3'] + weights2[1]*row['HBP_df2'])
            SH = gaussian_pdf(row['Age']) * (weights2[0]*row['SH_df3'] + weights2[1]*row['SH_df2'])
            SF = gaussian_pdf(row['Age']) * (weights2[0]*row['SF_df3'] + weights2[1]*row['SF_df2'])
            IBB = gaussian_pdf(row['Age']) * (weights2[0]*row['IBB_df3'] + weights2[1]*row['IBB_df2'])
        elif in_df3 and in_df1:
            games = gaussian_pdf(row['Age']) * (weights2[0]*row['G_df3'] + weights2[1]*row['G_df1'])
            PA = gaussian_pdf(row['Age']) * (weights2[0]*row['PA_df3'] + weights2[1]*row['PA_df1'])
            AB = gaussian_pdf(row['Age']) * (weights2[0]*row['AB_df3'] + weights2[1]*row['AB_df1'])
            R = gaussian_pdf(row['Age']) * (weights2[0]*row['R_df3'] + weights2[1]*row['R_df1'])
            H = gaussian_pdf(row['Age']) * (weights2[0]*row['H_df3'] + weights2[1]*row['H_df1'])
            Dub = gaussian_pdf(row['Age']) * (weights2[0]*row['2B_df3'] + weights2[1]*row['2B_df1'])
            Trip = gaussian_pdf(row['Age']) * (weights2[0]*row['3B_df3'] + weights2[1]*row['3B_df1'])
            HR = gaussian_pdf(row['Age']) * (weights2[0]*row['HR_df3'] + weights2[1]*row['HR_df1'])
            RBI = gaussian_pdf(row['Age']) * (weights2[0]*row['RBI_df3'] + weights2[1]*row['RBI_df1'])
            SB = gaussian_pdf(row['Age']) * (weights2[0]*row['SB_df3'] + weights2[1]*row['SB_df1'])
            CS = gaussian_pdf(row['Age']) * (weights2[0]*row['CS_df3'] + weights2[1]*row['CS_df1'])
            BB = gaussian_pdf(row['Age']) * (weights2[0]*row['BB_df3'] + weights2[1]*row['BB_df1'])
            SO = gaussian_pdf(row['Age']) * (weights2[0]*row['SO_df3'] + weights2[1]*row['SO_df1'])
            OPSplus = gaussian_pdf(row['Age']) * (weights2[0]*row['OPS+_df3'] + weights2[1]*row['OPS+_df1'])
            Rbat = gaussian_pdf(row['Age']) * (weights2[0]*row['Rbat+_df3'] + weights2[1]*row['Rbat+_df1'])
            TB = gaussian_pdf(row['Age']) * (weights2[0]*row['TB_df3'] + weights2[1]*row['TB_df1'])
            GIDP = gaussian_pdf(row['Age']) * (weights2[0]*row['GIDP_df3'] + weights2[1]*row['GIDP_df1'])
            HBP = gaussian_pdf(row['Age']) * (weights2[0]*row['HBP_df3'] + weights2[1]*row['HBP_df1'])
            SH = gaussian_pdf(row['Age']) * (weights2[0]*row['SH_df3'] + weights2[1]*row['SH_df1'])
            SF = gaussian_pdf(row['Age']) * (weights2[0]*row['SF_df3'] + weights2[1]*row['SF_df1'])
            IBB = gaussian_pdf(row['Age']) * (weights2[0]*row['IBB_df3'] + weights2[1]*row['IBB_df1'])
        elif in_df2 and in_df1:
            games = gaussian_pdf(row['Age']) * (weights2[0]*row['G_df2'] + weights2[1]*row['G_df1'])
            PA = gaussian_pdf(row['Age']) * (weights2[0]*row['PA_df2'] + weights2[1]*row['PA_df1'])
            AB = gaussian_pdf(row['Age']) * (weights2[0]*row['AB_df2'] + weights2[1]*row['AB_df1'])
            R = gaussian_pdf(row['Age']) * (weights2[0]*row['R_df2'] + weights2[1]*row['R_df1'])
            H = gaussian_pdf(row['Age']) * (weights2[0]*row['H_df2'] + weights2[1]*row['H_df1'])
            Dub = gaussian_pdf(row['Age']) * (weights2[0]*row['2B_df2'] + weights2[1]*row['2B_df1'])
            Trip = gaussian_pdf(row['Age']) * (weights2[0]*row['3B_df2'] + weights2[1]*row['3B_df1'])
            HR = gaussian_pdf(row['Age']) * (weights2[0]*row['HR_df2'] + weights2[1]*row['HR_df1'])
            RBI = gaussian_pdf(row['Age']) * (weights2[0]*row['RBI_df2'] + weights2[1]*row['RBI_df1'])
            SB = gaussian_pdf(row['Age']) * (weights2[0]*row['SB_df2'] + weights2[1]*row['SB_df1'])
            CS = gaussian_pdf(row['Age']) * (weights2[0]*row['CS_df2'] + weights2[1]*row['CS_df1'])
            BB = gaussian_pdf(row['Age']) * (weights2[0]*row['BB_df2'] + weights2[1]*row['BB_df1'])
            SO = gaussian_pdf(row['Age']) * (weights2[0]*row['SO_df2'] + weights2[1]*row['SO_df1'])
            OPSplus = gaussian_pdf(row['Age']) * (weights2[0]*row['OPS+_df2'] + weights2[1]*row['OPS+_df1'])
            Rbat = gaussian_pdf(row['Age']) * (weights2[0]*row['Rbat+_df2'] + weights2[1]*row['Rbat+_df1'])
            TB = gaussian_pdf(row['Age']) * (weights2[0]*row['TB_df2'] + weights2[1]*row['TB_df1'])
            GIDP = gaussian_pdf(row['Age']) * (weights2[0]*row['GIDP_df2'] + weights2[1]*row['GIDP_df1'])
            HBP = gaussian_pdf(row['Age']) * (weights2[0]*row['HBP_df2'] + weights2[1]*row['HBP_df1'])
            SH = gaussian_pdf(row['Age']) * (weights2[0]*row['SH_df2'] + weights2[1]*row['SH_df1'])
            SF = gaussian_pdf(row['Age']) * (weights2[0]*row['SF_df2'] + weights2[1]*row['SF_df1'])
            IBB = gaussian_pdf(row['Age']) * (weights2[0]*row['IBB_df2'] + weights2[1]*row['IBB_df1'])
        elif in_df3:
            games = gaussian_pdf(row['Age']) * (weights1[0]*row['G_df3'])
            PA = gaussian_pdf(row['Age']) * (weights1[0]*row['PA_df3'])
            AB = gaussian_pdf(row['Age']) * (weights1[0]*row['AB_df3'])
            R = gaussian_pdf(row['Age']) * (weights1[0]*row['R_df3'])
            H = gaussian_pdf(row['Age']) * (weights1[0]*row['H_df3'])
            Dub = gaussian_pdf(row['Age']) * (weights1[0]*row['2B_df3'])
            Trip = gaussian_pdf(row['Age']) * (weights1[0]*row['3B_df3'])
            HR = gaussian_pdf(row['Age']) * (weights1[0]*row['HR_df3'])
            RBI = gaussian_pdf(row['Age']) * (weights1[0]*row['RBI_df3'])
            SB = gaussian_pdf(row['Age']) * (weights1[0]*row['SB_df3'])
            CS = gaussian_pdf(row['Age']) * (weights1[0]*row['CS_df3'])
            BB = gaussian_pdf(row['Age']) * (weights1[0]*row['BB_df3'])
            SO = gaussian_pdf(row['Age']) * (weights1[0]*row['SO_df3'])
            OPSplus = gaussian_pdf(row['Age']) * (weights1[0]*row['OPS+_df3'])
            Rbat = gaussian_pdf(row['Age']) * (weights1[0]*row['Rbat+_df3'])
            TB = gaussian_pdf(row['Age']) * (weights1[0]*row['TB_df3'])
            GIDP = gaussian_pdf(row['Age']) * (weights1[0]*row['GIDP_df3'])
            HBP = gaussian_pdf(row['Age']) * (weights1[0]*row['HBP_df3'])
            SH = gaussian_pdf(row['Age']) * (weights1[0]*row['SH_df3'])
            SF = gaussian_pdf(row['Age']) * (weights1[0]*row['SF_df3'])
            IBB = gaussian_pdf(row['Age']) * (weights1[0]*row['IBB_df3'])
        elif in_df2:
            games = gaussian_pdf(row['Age']) * (weights1[0]*row['G_df2'])
            PA = gaussian_pdf(row['Age']) * (weights1[0]*row['PA_df2'])
            AB = gaussian_pdf(row['Age']) * (weights1[0]*row['AB_df2'])
            R = gaussian_pdf(row['Age']) * (weights1[0]*row['R_df2'])
            H = gaussian_pdf(row['Age']) * (weights1[0]*row['H_df2'])
            Dub = gaussian_pdf(row['Age']) * (weights1[0]*row['2B_df2'])
            Trip = gaussian_pdf(row['Age']) * (weights1[0]*row['3B_df2'])
            HR = gaussian_pdf(row['Age']) * (weights1[0]*row['HR_df2'])
            RBI = gaussian_pdf(row['Age']) * (weights1[0]*row['RBI_df2'])
            SB = gaussian_pdf(row['Age']) * (weights1[0]*row['SB_df2'])
            CS = gaussian_pdf(row['Age']) * (weights1[0]*row['CS_df2'])
            BB = gaussian_pdf(row['Age']) * (weights1[0]*row['BB_df2'])
            SO = gaussian_pdf(row['Age']) * (weights1[0]*row['SO_df2'])
            OPSplus = gaussian_pdf(row['Age']) * (weights1[0]*row['OPS+_df2'])
            Rbat = gaussian_pdf(row['Age']) * (weights1[0]*row['Rbat+_df2'])
            TB = gaussian_pdf(row['Age']) * (weights1[0]*row['TB_df2'])
            GIDP = gaussian_pdf(row['Age']) * (weights1[0]*row['GIDP_df2'])
            HBP = gaussian_pdf(row['Age']) * (weights1[0]*row['HBP_df2'])
            SH = gaussian_pdf(row['Age']) * (weights1[0]*row['SH_df2'])
            SF = gaussian_pdf(row['Age']) * (weights1[0]*row['SF_df2'])
            IBB = gaussian_pdf(row['Age']) * (weights1[0]*row['IBB_df2'])
        elif in_df1:
            games = gaussian_pdf(row['Age']) * (weights1[0]*row['G_df1'])
            PA = gaussian_pdf(row['Age']) * (weights1[0]*row['PA_df1'])
            AB = gaussian_pdf(row['Age']) * (weights1[0]*row['AB_df1'])
            R = gaussian_pdf(row['Age']) * (weights1[0]*row['R_df1'])
            H = gaussian_pdf(row['Age']) * (weights1[0]*row['H_df1'])
            Dub = gaussian_pdf(row['Age']) * (weights1[0]*row['2B_df1'])
            Trip = gaussian_pdf(row['Age']) * (weights1[0]*row['3B_df1'])
            HR = gaussian_pdf(row['Age']) * (weights1[0]*row['HR_df1'])
            RBI = gaussian_pdf(row['Age']) * (weights1[0]*row['RBI_df1'])
            SB = gaussian_pdf(row['Age']) * (weights1[0]*row['SB_df1'])
            CS = gaussian_pdf(row['Age']) * (weights1[0]*row['CS_df1'])
            BB = gaussian_pdf(row['Age']) * (weights1[0]*row['BB_df1'])
            SO = gaussian_pdf(row['Age']) * (weights1[0]*row['SO_df1'])
            OPSplus = gaussian_pdf(row['Age']) * (weights1[0]*row['OPS+_df1'])
            Rbat = gaussian_pdf(row['Age']) * (weights1[0]*row['Rbat+_df1'])
            TB = gaussian_pdf(row['Age']) * (weights1[0]*row['TB_df1'])
            GIDP = gaussian_pdf(row['Age']) * (weights1[0]*row['GIDP_df1'])
            HBP = gaussian_pdf(row['Age']) * (weights1[0]*row['HBP_df1'])
            SH = gaussian_pdf(row['Age']) * (weights1[0]*row['SH_df1'])
            SF = gaussian_pdf(row['Age']) * (weights1[0]*row['SF_df1'])
            IBB = gaussian_pdf(row['Age']) * (weights1[0]*row['IBB_df1'])
        else:
            games = np.zeros(num_sim)
            PA = np.zeros(num_sim)
            AB = np.zeros(num_sim)
            R = np.zeros(num_sim)
            H = np.zeros(num_sim)
            Dub = np.zeros(num_sim)
            Trip = np.zeros(num_sim)
            HR = np.zeros(num_sim)
            RBI = np.zeros(num_sim)
            SB = np.zeros(num_sim)
            CS = np.zeros(num_sim)
            BB = np.zeros(num_sim)
            SO = np.zeros(num_sim)
            OPSplus = np.zeros(num_sim)
            Rbat = np.zeros(num_sim)
            TB = np.zeros(num_sim)
            GIDP = np.zeros(num_sim)
            HBP = np.zeros(num_sim)
            SH = np.zeros(num_sim)
            SF = np.zeros(num_sim)
            IBB = np.zeros(num_sim)

        
        predictedgames.append(games.mean())
        predictedPA.append(PA.mean())
        predictedAB.append(AB.mean())
        predictedR.append(R.mean())
        predictedH.append(H.mean())
        predictedDub.append(Dub.mean())
        predictedTrip.append(Trip.mean())
        predictedHR.append(HR.mean())
        predictedRBI.append(RBI.mean())
        predictedSB.append(SB.mean())
        predictedCS.append(CS.mean())
        predictedBB.append(BB.mean())
        predictedSO.append(SO.mean())
        predictedOPSplus.append(OPSplus.mean())
        predictedRbat.append(Rbat.mean())
        predictedTB.append(TB.mean())
        predictedGIDP.append(GIDP.mean())
        predictedHBP.append(HBP.mean())
        predictedSH.append(SH.mean())
        predictedSF.append(SF.mean())
        predictedIBB.append(IBB.mean())

    future['G'] = predictedgames
    future['PA'] = predictedPA
    future['AB'] = predictedAB
    future['R'] = predictedR
    future['H'] = predictedH
    future['2B'] = predictedDub
    future['3B'] = predictedTrip
    future['HR'] = predictedHR
    future['RBI'] = predictedRBI
    future['SB'] = predictedSB
    future['CS'] = predictedCS
    future['BB'] = predictedBB
    future['SO'] = predictedSO
    future['OPS+'] = predictedOPSplus
    future['Rbat+'] = predictedRbat
    future['TB'] = predictedTB
    future['GIDP'] = predictedGIDP
    future['HBP'] = predictedSH
    future['SH'] = predictedSH
    future['SF'] = predictedSF
    future['IBB'] = predictedIBB

    future['BA'] = future['H']/future['AB']
    future['OBP'] = (future['H']+future['BB']+future['HBP']+future['IBB']) / (future['AB']+future['BB']+future['HBP']+future['IBB']+future['SF'])
    future['SLG'] = future['TB']/future['AB']
    future['OPS'] = future['OBP'] + future['SLG']

    scale = future['G'].apply(lambda x: min(1, 162 / x) if x > 0 else 1)
    stats_cols = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'SO', 'OPS+', 'Rbat+', 'TB', 'GIDP', 'HBP', 'SH', 'SF', 'IBB']

    future[stats_cols] = future[stats_cols].multiply(scale, axis=0)



    future['G'] = future['G'].round(1)
    future['PA'] = future['PA'].round(1)
    future['AB'] = future['AB'].round(1)
    future['R'] = future['R'].round(1)
    future['H'] = future['H'].round(1)
    future['2B'] = future['2B'].round(1)
    future['3B'] = future['3B'].round(1)
    future['HR'] = future['HR'].round(1)
    future['RBI'] = future['RBI'].round(1)
    future['SB'] = future['SB'].round(1)
    future['CS'] = future['CS'].round(1)
    future['BB'] = future['BB'].round(1)
    future['SO'] = future['SO'].round(1)
    future['OPS+'] = future['OPS+'].round(1)
    future['Rbat+'] = future['Rbat+'].round(1)
    future['TB'] = future['TB'].round(1)
    future['GIDP'] = future['GIDP'].round(1)
    future['HBP'] = future['HBP'].round(1)
    future['SH'] = future['SH'].round(1)
    future['SF'] = future['SF'].round(1)
    future['IBB'] = future['IBB'].round(1)

    future['BA'] = future['BA'].round(4)
    future['OBP'] = future['OBP'].round(4)
    future['SLG'] = future['SLG'].round(4)
    future['OPS'] = future['OPS'].round(4)

    future['Rank'] = range(1, len(future) + 1)
    coles = ['Rank'] + [col for col in future.columns if col != 'Rank']
    future = future[coles]
    future = future.drop('PlayerID', axis=1) 
    future = future.drop('rOBA', axis=1) 
    future[future.select_dtypes('number').columns] = future.select_dtypes('number').fillna(0)

    future = future.assign(Position=future['Pos'].apply(lambda x: ', '.join(p.split('-')[0] for p in x.split())))[list(future.columns[:2]) + ['Position'] + list(future.columns[2:])]

    future = future.drop('Pos', axis=1) 

    return future


def preseasonmlbhittinghtml(future):

        html_string = future.to_html(classes='display', index=False).replace('class="dataframe display"', 'class="display"')

        # Full HTML file with sorting and ALL rows shown
        html_script = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title> Preseason Predictions </title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="icon" type="image/png" sizes="96x96" href="/WebProjects/images/favicon-96x96.png" />
        <link rel="icon" type="image/svg+xml" href="/WebProjects/images/favicon.svg" />
        <link rel="shortcut icon" href="/WebProjects/images/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/WebProjects/images/apple-touch-icon.png" />
        <meta name="apple-mobile-web-app-title" content="MyWebSit" />
        <link rel="manifest" href="/WebProjects/images/site.webmanifest" />

        <link rel="stylesheet" href="/WebProjects/style.css">


        </head>
        <body>

        <div class="topnav">
        <a href="/WebProjects/index.html">Home</a>
            <div class="dropdown">
                <button class="dropbtn">Football
                    <i class="fa fa-caret-down"></i>
                </button>
                <div class="dropdown-content">
                    <a href="/WebProjects/WeeklyPred_html/SuperFlex.html">Weekly Predictions</a>
                    <a href="/WebProjects/ROS_html/Rest Of Season.html">Rest of Season Predictions</a>
                    <a href="/WebProjects/WeeklyScores_html/Weekly Game Predictions.html">Weekly Game Predictions</a>
                    <a href="/WebProjects/Dominance_html/QBDom.html">Offensive Focus</a>
                </div>
            </div>
            <div class="dropdown">
                <button class="dropbtn active">Baseball
                    <i class="fa fa-caret-down"></i>
                </button>
                <div class="dropdown-content">
                    <a href="/WebProjects/PreseasonMLBHittingPredictions.html">MLB Preseason Hitting Predictions</a>
                    <a href="/WebProjects/PreseasonMLBPitchingPredictions.html">MLB Preseason Pitching Predictions</a>
                </div>
            </div>
        <a href="/WebProjects/Fitness_html/fitness.html">Fitness</a>
        <a href="/WebProjects/about.html">About</a>
        </div>
        

        <img src="/WebProjects/images/Banner_Logo.png" alt="Header Image" class="header-img">

        <h1>MLB Hitting Predictions</h1>

        <div class="topnav">
        <input type="text" id="searchBar" placeholder="Search...">
        </div>



        {html_string}

        <script>
        function getCellValue(row, index) {{
            return row.cells[index].textContent.trim();
        }}

        function comparer(index, asc) {{
            return function(a, b) {{
            const v1 = getCellValue(a, index);
            const v2 = getCellValue(b, index);

            const num1 = parseFloat(v1);
            const num2 = parseFloat(v2);
            const bothNumbers = !isNaN(num1) && !isNaN(num2);

            if (bothNumbers) {{
                return asc ? num1 - num2 : num2 - num1;
            }} else {{
                return asc ? v1.localeCompare(v2) : v2.localeCompare(v1);
            }}
            }};
        }}

        document.addEventListener("DOMContentLoaded", function () {{
            document.querySelectorAll("th").forEach(function (th, index) {{
            let ascending = true;
            if (index === 0) return;
            th.addEventListener("click", function () {{
                const table = th.closest("table");
                const tbody = table.querySelector("tbody");
                const rows = Array.from(tbody.querySelectorAll("tr"));
                rows.sort(comparer(index, ascending));
                //rows.forEach(row => tbody.appendChild(row));
                rows.forEach((row, i) => {{
                    row.cells[0].textContent = i + 1; // Reset Rank to match new row position
                    tbody.appendChild(row);
                }});
                ascending = !ascending;
            }});
            }});
        }});
        </script>

        

        <script>
        const searchBar = document.getElementById('searchBar');
        const table = document.querySelector('table');
        const rows = table.getElementsByTagName('tr');

        searchBar.addEventListener('keyup', function () {{
            const searchText = searchBar.value.toLowerCase();

            for (let i = 1; i < rows.length; i++) {{
            const row = rows[i];
            const rowText = row.textContent.toLowerCase();
            row.style.display = rowText.includes(searchText) ? '' : 'none';
            }}
        }});
        </script>

        

        </body>
        </html>
        """

        # Save to HTML file
        with open(f"PreseasonMLBHittingPredictions.html", "w", encoding="utf-8") as f:
            f.write(html_script)


def pitcherpredictions(csv1, csv2, csv3, csv4):

    if not isinstance(csv1, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv1)}: {csv1}")
    if not csv1.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv1}")
    if not os.path.exists(csv1):
        raise ValueError(f"File not found: {csv1}")

    if not isinstance(csv2, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv2)}: {csv2}")
    if not csv2.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv2}")
    if not os.path.exists(csv2):
        raise ValueError(f"File not found: {csv2}")

    if not isinstance(csv3, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv3)}: {csv3}")
    if not csv3.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv3}")
    if not os.path.exists(csv3):
        raise ValueError(f"File not found: {csv3}")

    if not isinstance(csv4, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv4)}: {csv4}")
    if not csv4.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv4}")
    if not os.path.exists(csv4):
        raise ValueError(f"File not found: {csv4}")

    df1 = pd.read_csv(csv1)
    df1["Player"] = df1["Player"].str.replace(r"[\*#]+$", "", regex=True).str.strip()
    df1['Player'] = df1['Player'].apply(lambda x: "".join(c for c in unicodedata.normalize("NFKC", str(x)) if c not in "*#\u200B\u200C\u200D\uFEFF"))
    df2 = pd.read_csv(csv2)
    df2["Player"] = df2["Player"].str.replace(r"[\*#]+$", "", regex=True).str.strip()
    df2['Player'] = df2['Player'].apply(lambda x: "".join(c for c in unicodedata.normalize("NFKC", str(x)) if c not in "*#\u200B\u200C\u200D\uFEFF"))
    df3 = pd.read_csv(csv3)
    df3["Player"] = df3["Player"].str.replace(r"[\*#]+$", "", regex=True).str.strip()
    df3['Player'] = df3['Player'].apply(lambda x: "".join(c for c in unicodedata.normalize("NFKC", str(x)) if c not in "*#\u200B\u200C\u200D\uFEFF"))
    df4 = pd.read_csv(csv4)
    df4["Name"] = df4["Name"].str.replace(r"[\*#]+$", "", regex=True).str.strip()
    df4['Name'] = df4['Name'].apply(lambda x: "".join(c for c in unicodedata.normalize("NFKC", str(x)) if c not in "*#\u200B\u200C\u200D\uFEFF"))

    #row1 = df1[df1['Player'] == 'CJ Abrams']
    #row2 = df2[df2['Player'] == 'CJ Abrams']
    #row3 = df3[df3['Player'] == 'CJ Abrams']
    #row4 = df4[df4['Name'] == 'CJ Abrams']

    #print(row1)
    #print(row2)
    #print(row3)
    #print(row4)

    future = pd.DataFrame(columns=df3.columns)
    future['Player'] = df4['Name']
    future['Age'] = df4['Age']
    future['Team'] = df4['Tm']
    future = future.drop('Rk', axis=1) 
    future = future.drop('Lg', axis=1) 
    future = future.drop('WAR', axis=1) 
    future = future.drop('Awards', axis=1) 
    future = future.drop('Player-additional', axis=1) 


    future['Player'] = future['Player'].astype(str)
    df1['Player'] = df1['Player'].astype(str)
    df2['Player'] = df2['Player'].astype(str)
    df3['Player'] = df3['Player'].astype(str)

    future['PlayerID'] = future['Player'] + "_" + future['Team']
    df1['PlayerID'] = df1['Player'] + "_" + df1['Team']
    df2['PlayerID'] = df2['Player'] + "_" + df2['Team']
    df3['PlayerID'] = df2['Player'] + "_" + df3['Team']

    future['PlayerID'] = future['PlayerID'].astype(str)
    df1['PlayerID'] = df1['PlayerID'].astype(str)
    df2['PlayerID'] = df2['PlayerID'].astype(str)
    df3['PlayerID'] = df3['PlayerID'].astype(str)


    def gaussian_pdf(age):
        return np.exp(-0.5 * ((age - 28)/5)**2)

    #cols = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'SO', 'OPS+', 'Rbat+', 'TB', 'GIDP', 'HBP', 'SH', 'SF', 'IBB']
    cols = ["W", "L", "ERA", "G", "GS", "GF", "CG", "SHO", "SV", "IP", "H", "R", "ER", "HR", "BB", "IBB", "SO", "HBP", "BK", "WP", "BF", "ERA+", "FIP", "WHIP", "H9", "HR9", "BB9", "SO9"]
    # Merge future with df1, df2, df3
    merged_df = future.copy()

    # List of dataframes to merge with suffixes
    dfs = [(df1, '_df1'), (df2, '_df2'), (df3, '_df3')]

    # Merge each dataframe
    for df, suffix in dfs:
        merged_df = pd.merge(merged_df, df, on='Player', how='left', suffixes=('', suffix))

    # Rename the columns for the specified ones
    for col in cols:
        for suffix in ['_df1', '_df2', '_df3']:
            if f'{col}{suffix}' in merged_df.columns:
                merged_df.rename(columns={f'{col}{suffix}': f'{col}{suffix}'}, inplace=True)

    # Now `merged_df` has all the columns merged and renamed appropriately


    #future['is_in_df3'] = future['Player'].isin(df3['Player'])
    #future['is_in_df2'] = future['Player'].isin(df2['Player'])
    #future['is_in_df1'] = future['Player'].isin(df1['Player'])

    num_sim = 1000

    weights = [np.random.uniform(0.6, 0.8, num_sim), np.random.uniform(0.4, 0.5, num_sim), np.random.uniform(0,0.2, num_sim)]
    weights2 = [np.random.uniform(0.7, 0.9, num_sim), np.random.uniform(0.1, 0.3, num_sim)]
    weights1 = [np.random.uniform(0.9, 1.1, num_sim)]

    predictedW = []
    predictedL = []
    predictedG = []
    predictedGS = []
    predictedGF = []
    predictedCG = []
    predictedSHO = []
    predictedSV = []
    predictedIP = []
    predictedH = []
    predictedR = []
    predictedER = []
    predictedHR = []
    predictedBB = []
    predictedIBB = []
    predictedSO = []
    predictedHBP = []
    predictedBK = []
    predictedWP = []
    predictedBF = []
    predictedERAplus = []
    predictedFIP = []

    #duplicates = merged_df['PlayerID'][merged_df['PlayerID'].duplicated(keep=False)]
    #print(duplicates)
    #merged_df = merged_df.fillna(0)
    merged_df[merged_df.select_dtypes('number').columns] = merged_df.select_dtypes('number').fillna(0)
    merged_df = merged_df.drop_duplicates(subset='PlayerID')
    merged_df = merged_df.reset_index(drop=True)

    #print(merged_df.head(5))

    for i, row in merged_df.iterrows():
        player = row['Player']  # Get the player name

        in_df1 = df1['Player'].isin([player]).any()
        in_df2 = df2['Player'].isin([player]).any()
        in_df3 = df3['Player'].isin([player]).any()


        if in_df1 and in_df2 and in_df3:
            W = gaussian_pdf(row['Age']) * (weights[0]*row['W_df3'] + weights[1]*row['W_df2'] + weights[2]*row['W_df1'])
            L = gaussian_pdf(row['Age']) * (weights[0]*row['L_df3'] + weights[1]*row['L_df2'] + weights[2]*row['L_df1'])
            G = gaussian_pdf(row['Age']) * (weights[0]*row['G_df3'] + weights[1]*row['G_df2'] + weights[2]*row['G_df1'])
            GS = gaussian_pdf(row['Age']) * (weights[0]*row['GS_df3'] + weights[1]*row['GS_df2'] + weights[2]*row['GS_df1'])
            GF = gaussian_pdf(row['Age']) * (weights[0]*row['GF_df3'] + weights[1]*row['GF_df2'] + weights[2]*row['GF_df1'])
            CG = gaussian_pdf(row['Age']) * (weights[0]*row['CG_df3'] + weights[1]*row['CG_df2'] + weights[2]*row['CG_df1'])
            SHO = gaussian_pdf(row['Age']) * (weights[0]*row['SHO_df3'] + weights[1]*row['SHO_df2'] + weights[2]*row['SHO_df1'])
            SV = gaussian_pdf(row['Age']) * (weights[0]*row['SV_df3'] + weights[1]*row['SV_df2'] + weights[2]*row['SV_df1'])
            IP = gaussian_pdf(row['Age']) * (weights[0]*row['IP_df3'] + weights[1]*row['IP_df2'] + weights[2]*row['IP_df1'])
            H = gaussian_pdf(row['Age']) * (weights[0]*row['H_df3'] + weights[1]*row['H_df2'] + weights[2]*row['H_df1'])
            R = gaussian_pdf(row['Age']) * (weights[0]*row['R_df3'] + weights[1]*row['R_df2'] + weights[2]*row['R_df1'])
            ER = gaussian_pdf(row['Age']) * (weights[0]*row['ER_df3'] + weights[1]*row['ER_df2'] + weights[2]*row['ER_df1'])
            HR = gaussian_pdf(row['Age']) * (weights[0]*row['HR_df3'] + weights[1]*row['HR_df2'] + weights[2]*row['HR_df1'])
            BB = gaussian_pdf(row['Age']) * (weights[0]*row['BB_df3'] + weights[1]*row['BB_df2'] + weights[2]*row['BB_df1'])
            IBB = gaussian_pdf(row['Age']) * (weights[0]*row['IBB_df3'] + weights[1]*row['IBB_df2'] + weights[2]*row['IBB_df1'])
            SO = gaussian_pdf(row['Age']) * (weights[0]*row['SO_df3'] + weights[1]*row['SO_df2'] + weights[2]*row['SO_df1'])
            HBP = gaussian_pdf(row['Age']) * (weights[0]*row['HBP_df3'] + weights[1]*row['HBP_df2'] + weights[2]*row['HBP_df1'])
            BK = gaussian_pdf(row['Age']) * (weights[0]*row['BK_df3'] + weights[1]*row['BK_df2'] + weights[2]*row['BK_df1'])
            WP = gaussian_pdf(row['Age']) * (weights[0]*row['WP_df3'] + weights[1]*row['WP_df2'] + weights[2]*row['WP_df1'])
            BF = gaussian_pdf(row['Age']) * (weights[0]*row['BF_df3'] + weights[1]*row['BF_df2'] + weights[2]*row['BF_df1'])
            ERAplus = gaussian_pdf(row['Age']) * (weights[0]*row['ERA+_df3'] + weights[1]*row['ERA+_df2'] + weights[2]*row['ERA+_df1'])
            FIP = gaussian_pdf(row['Age']) * (weights[0]*row['FIP_df3'] + weights[1]*row['FIP_df2'] + weights[2]*row['FIP_df1'])
        elif in_df3 and in_df2:
            W = gaussian_pdf(row['Age']) * (weights2[0]*row['W_df3'] + weights2[1]*row['W_df2'])
            L = gaussian_pdf(row['Age']) * (weights2[0]*row['L_df3'] + weights2[1]*row['L_df2'])
            G = gaussian_pdf(row['Age']) * (weights2[0]*row['G_df3'] + weights2[1]*row['G_df2'])
            GS = gaussian_pdf(row['Age']) * (weights2[0]*row['GS_df3'] + weights2[1]*row['GS_df2'])
            GF = gaussian_pdf(row['Age']) * (weights2[0]*row['GF_df3'] + weights2[1]*row['GF_df2'])
            CG = gaussian_pdf(row['Age']) * (weights2[0]*row['CG_df3'] + weights2[1]*row['CG_df2'])
            SHO = gaussian_pdf(row['Age']) * (weights2[0]*row['SHO_df3'] + weights2[1]*row['SHO_df2'])
            SV = gaussian_pdf(row['Age']) * (weights2[0]*row['SV_df3'] + weights2[1]*row['SV_df2'])
            IP = gaussian_pdf(row['Age']) * (weights2[0]*row['IP_df3'] + weights2[1]*row['IP_df2'])
            H = gaussian_pdf(row['Age']) * (weights2[0]*row['H_df3'] + weights2[1]*row['H_df2'])
            R = gaussian_pdf(row['Age']) * (weights2[0]*row['R_df3'] + weights2[1]*row['R_df2'])
            ER = gaussian_pdf(row['Age']) * (weights2[0]*row['ER_df3'] + weights2[1]*row['ER_df2'])
            HR = gaussian_pdf(row['Age']) * (weights2[0]*row['HR_df3'] + weights2[1]*row['HR_df2'])
            BB = gaussian_pdf(row['Age']) * (weights2[0]*row['BB_df3'] + weights2[1]*row['BB_df2'])
            IBB = gaussian_pdf(row['Age']) * (weights2[0]*row['IBB_df3'] + weights2[1]*row['IBB_df2'])
            SO = gaussian_pdf(row['Age']) * (weights2[0]*row['SO_df3'] + weights2[1]*row['SO_df2'])
            HBP = gaussian_pdf(row['Age']) * (weights2[0]*row['HBP_df3'] + weights2[1]*row['HBP_df2'])
            BK = gaussian_pdf(row['Age']) * (weights2[0]*row['BK_df3'] + weights2[1]*row['BK_df2'])
            WP = gaussian_pdf(row['Age']) * (weights2[0]*row['WP_df3'] + weights2[1]*row['WP_df2'])
            BF = gaussian_pdf(row['Age']) * (weights2[0]*row['BF_df3'] + weights2[1]*row['BF_df2'])
            ERAplus = gaussian_pdf(row['Age']) * (weights2[0]*row['ERA+_df3'] + weights2[1]*row['ERA+_df2'])
            FIP = gaussian_pdf(row['Age']) * (weights2[0]*row['FIP_df3'] + weights2[1]*row['FIP_df2'])
        elif in_df3 and in_df1:
            W = gaussian_pdf(row['Age']) * (weights2[0]*row['W_df3'] + weights2[1]*row['W_df1'])
            L = gaussian_pdf(row['Age']) * (weights2[0]*row['L_df3'] + weights2[1]*row['L_df1'])
            G = gaussian_pdf(row['Age']) * (weights2[0]*row['G_df3'] + weights2[1]*row['G_df1'])
            GS = gaussian_pdf(row['Age']) * (weights2[0]*row['GS_df3'] + weights2[1]*row['GS_df1'])
            GF = gaussian_pdf(row['Age']) * (weights2[0]*row['GF_df3'] + weights2[1]*row['GF_df1'])
            CG = gaussian_pdf(row['Age']) * (weights2[0]*row['CG_df3'] + weights2[1]*row['CG_df1'])
            SHO = gaussian_pdf(row['Age']) * (weights2[0]*row['SHO_df3'] + weights2[1]*row['SHO_df1'])
            SV = gaussian_pdf(row['Age']) * (weights2[0]*row['SV_df3'] + weights2[1]*row['SV_df1'])
            IP = gaussian_pdf(row['Age']) * (weights2[0]*row['IP_df3'] + weights2[1]*row['IP_df1'])
            H = gaussian_pdf(row['Age']) * (weights2[0]*row['H_df3'] + weights2[1]*row['H_df1'])
            R = gaussian_pdf(row['Age']) * (weights2[0]*row['R_df3'] + weights2[1]*row['R_df1'])
            ER = gaussian_pdf(row['Age']) * (weights2[0]*row['ER_df3'] + weights2[1]*row['ER_df1'])
            HR = gaussian_pdf(row['Age']) * (weights2[0]*row['HR_df3'] + weights2[1]*row['HR_df1'])
            BB = gaussian_pdf(row['Age']) * (weights2[0]*row['BB_df3'] + weights2[1]*row['BB_df1'])
            IBB = gaussian_pdf(row['Age']) * (weights2[0]*row['IBB_df3'] + weights2[1]*row['IBB_df1'])
            SO = gaussian_pdf(row['Age']) * (weights2[0]*row['SO_df3'] + weights2[1]*row['SO_df1'])
            HBP = gaussian_pdf(row['Age']) * (weights2[0]*row['HBP_df3'] + weights2[1]*row['HBP_df1'])
            BK = gaussian_pdf(row['Age']) * (weights2[0]*row['BK_df3'] + weights2[1]*row['BK_df1'])
            WP = gaussian_pdf(row['Age']) * (weights2[0]*row['WP_df3'] + weights2[1]*row['WP_df1'])
            BF = gaussian_pdf(row['Age']) * (weights2[0]*row['BF_df3'] + weights2[1]*row['BF_df1'])
            ERAplus = gaussian_pdf(row['Age']) * (weights2[0]*row['ERA+_df3'] + weights2[1]*row['ERA+_df1'])
            FIP = gaussian_pdf(row['Age']) * (weights2[0]*row['FIP_df3'] + weights2[1]*row['FIP_df1'])
        elif in_df2 and in_df1:
            W = gaussian_pdf(row['Age']) * (weights2[0]*row['W_df2'] + weights2[1]*row['W_df1'])
            L = gaussian_pdf(row['Age']) * (weights2[0]*row['L_df2'] + weights2[1]*row['L_df1'])
            G = gaussian_pdf(row['Age']) * (weights2[0]*row['G_df2'] + weights2[1]*row['G_df1'])
            GS = gaussian_pdf(row['Age']) * (weights2[0]*row['GS_df2'] + weights2[1]*row['GS_df1'])
            GF = gaussian_pdf(row['Age']) * (weights2[0]*row['GF_df2'] + weights2[1]*row['GF_df1'])
            CG = gaussian_pdf(row['Age']) * (weights2[0]*row['CG_df2'] + weights2[1]*row['CG_df1'])
            SHO = gaussian_pdf(row['Age']) * (weights2[0]*row['SHO_df2'] + weights2[1]*row['SHO_df1'])
            SV = gaussian_pdf(row['Age']) * (weights2[0]*row['SV_df2'] + weights2[1]*row['SV_df1'])
            IP = gaussian_pdf(row['Age']) * (weights2[0]*row['IP_df2'] + weights2[1]*row['IP_df1'])
            H = gaussian_pdf(row['Age']) * (weights2[0]*row['H_df2'] + weights2[1]*row['H_df1'])
            R = gaussian_pdf(row['Age']) * (weights2[0]*row['R_df2'] + weights2[1]*row['R_df1'])
            ER = gaussian_pdf(row['Age']) * (weights2[0]*row['ER_df2'] + weights2[1]*row['ER_df1'])
            HR = gaussian_pdf(row['Age']) * (weights2[0]*row['HR_df2'] + weights2[1]*row['HR_df1'])
            BB = gaussian_pdf(row['Age']) * (weights2[0]*row['BB_df2'] + weights2[1]*row['BB_df1'])
            IBB = gaussian_pdf(row['Age']) * (weights2[0]*row['IBB_df2'] + weights2[1]*row['IBB_df1'])
            SO = gaussian_pdf(row['Age']) * (weights2[0]*row['SO_df2'] + weights2[1]*row['SO_df1'])
            HBP = gaussian_pdf(row['Age']) * (weights2[0]*row['HBP_df2'] + weights2[1]*row['HBP_df1'])
            BK = gaussian_pdf(row['Age']) * (weights2[0]*row['BK_df2'] + weights2[1]*row['BK_df1'])
            WP = gaussian_pdf(row['Age']) * (weights2[0]*row['WP_df2'] + weights2[1]*row['WP_df1'])
            BF = gaussian_pdf(row['Age']) * (weights2[0]*row['BF_df2'] + weights2[1]*row['BF_df1'])
            ERAplus = gaussian_pdf(row['Age']) * (weights2[0]*row['ERA+_df2'] + weights2[1]*row['ERA+_df1'])
            FIP = gaussian_pdf(row['Age']) * (weights2[0]*row['FIP_df2'] + weights2[1]*row['FIP_df1'])
        elif in_df3:
            W = gaussian_pdf(row['Age']) * (weights1[0]*row['W_df3'])
            L = gaussian_pdf(row['Age']) * (weights1[0]*row['L_df3'])
            G = gaussian_pdf(row['Age']) * (weights1[0]*row['G_df3'])
            GS = gaussian_pdf(row['Age']) * (weights1[0]*row['GS_df3'])
            GF = gaussian_pdf(row['Age']) * (weights1[0]*row['GF_df3'])
            CG = gaussian_pdf(row['Age']) * (weights1[0]*row['CG_df3'])
            SHO = gaussian_pdf(row['Age']) * (weights1[0]*row['SHO_df3'])
            SV = gaussian_pdf(row['Age']) * (weights1[0]*row['SV_df3'])
            IP = gaussian_pdf(row['Age']) * (weights1[0]*row['IP_df3'])
            H = gaussian_pdf(row['Age']) * (weights1[0]*row['H_df3'])
            R = gaussian_pdf(row['Age']) * (weights1[0]*row['R_df3'])
            ER = gaussian_pdf(row['Age']) * (weights1[0]*row['ER_df3'])
            HR = gaussian_pdf(row['Age']) * (weights1[0]*row['HR_df3'])
            BB = gaussian_pdf(row['Age']) * (weights1[0]*row['BB_df3'])
            IBB = gaussian_pdf(row['Age']) * (weights1[0]*row['IBB_df3'])
            SO = gaussian_pdf(row['Age']) * (weights1[0]*row['SO_df3'])
            HBP = gaussian_pdf(row['Age']) * (weights1[0]*row['HBP_df3'])
            BK = gaussian_pdf(row['Age']) * (weights1[0]*row['BK_df3'])
            WP = gaussian_pdf(row['Age']) * (weights1[0]*row['WP_df3'])
            BF = gaussian_pdf(row['Age']) * (weights1[0]*row['BF_df3'])
            ERAplus = gaussian_pdf(row['Age']) * (weights1[0]*row['ERA+_df3'])
            FIP = gaussian_pdf(row['Age']) * (weights1[0]*row['FIP_df3'])
        elif in_df2:
            W = gaussian_pdf(row['Age']) * (weights1[0]*row['W_df2'])
            L = gaussian_pdf(row['Age']) * (weights1[0]*row['L_df2'])
            G = gaussian_pdf(row['Age']) * (weights1[0]*row['G_df2'])
            GS = gaussian_pdf(row['Age']) * (weights1[0]*row['GS_df2'])
            GF = gaussian_pdf(row['Age']) * (weights1[0]*row['GF_df2'])
            CG = gaussian_pdf(row['Age']) * (weights1[0]*row['CG_df2'])
            SHO = gaussian_pdf(row['Age']) * (weights1[0]*row['SHO_df2'])
            SV = gaussian_pdf(row['Age']) * (weights1[0]*row['SV_df2'])
            IP = gaussian_pdf(row['Age']) * (weights1[0]*row['IP_df2'])
            H = gaussian_pdf(row['Age']) * (weights1[0]*row['H_df2'])
            R = gaussian_pdf(row['Age']) * (weights1[0]*row['R_df2'])
            ER = gaussian_pdf(row['Age']) * (weights1[0]*row['ER_df2'])
            HR = gaussian_pdf(row['Age']) * (weights1[0]*row['HR_df2'])
            BB = gaussian_pdf(row['Age']) * (weights1[0]*row['BB_df2'])
            IBB = gaussian_pdf(row['Age']) * (weights1[0]*row['IBB_df2'])
            SO = gaussian_pdf(row['Age']) * (weights1[0]*row['SO_df2'])
            HBP = gaussian_pdf(row['Age']) * (weights1[0]*row['HBP_df2'])
            BK = gaussian_pdf(row['Age']) * (weights1[0]*row['BK_df2'])
            WP = gaussian_pdf(row['Age']) * (weights1[0]*row['WP_df2'])
            BF = gaussian_pdf(row['Age']) * (weights1[0]*row['BF_df2'])
            ERAplus = gaussian_pdf(row['Age']) * (weights1[0]*row['ERA+_df2'])
            FIP = gaussian_pdf(row['Age']) * (weights1[0]*row['FIP_df2'])
        elif in_df1:
            W = gaussian_pdf(row['Age']) * (weights1[0]*row['W_df1'])
            L = gaussian_pdf(row['Age']) * (weights1[0]*row['L_df1'])
            G = gaussian_pdf(row['Age']) * (weights1[0]*row['G_df1'])
            GS = gaussian_pdf(row['Age']) * (weights1[0]*row['GS_df1'])
            GF = gaussian_pdf(row['Age']) * (weights1[0]*row['GF_df1'])
            CG = gaussian_pdf(row['Age']) * (weights1[0]*row['CG_df1'])
            SHO = gaussian_pdf(row['Age']) * (weights1[0]*row['SHO_df1'])
            SV = gaussian_pdf(row['Age']) * (weights1[0]*row['SV_df1'])
            IP = gaussian_pdf(row['Age']) * (weights1[0]*row['IP_df1'])
            H = gaussian_pdf(row['Age']) * (weights1[0]*row['H_df1'])
            R = gaussian_pdf(row['Age']) * (weights1[0]*row['R_df1'])
            ER = gaussian_pdf(row['Age']) * (weights1[0]*row['ER_df1'])
            HR = gaussian_pdf(row['Age']) * (weights1[0]*row['HR_df1'])
            BB = gaussian_pdf(row['Age']) * (weights1[0]*row['BB_df1'])
            IBB = gaussian_pdf(row['Age']) * (weights1[0]*row['IBB_df1'])
            SO = gaussian_pdf(row['Age']) * (weights1[0]*row['SO_df1'])
            HBP = gaussian_pdf(row['Age']) * (weights1[0]*row['HBP_df1'])
            BK = gaussian_pdf(row['Age']) * (weights1[0]*row['BK_df1'])
            WP = gaussian_pdf(row['Age']) * (weights1[0]*row['WP_df1'])
            BF = gaussian_pdf(row['Age']) * (weights1[0]*row['BF_df1'])
            ERAplus = gaussian_pdf(row['Age']) * (weights1[0]*row['ERA+_df1'])
            FIP = gaussian_pdf(row['Age']) * (weights1[0]*row['FIP_df1'])
        else:
            W = np.zeros(num_sim)
            L = np.zeros(num_sim)
            G = np.zeros(num_sim)
            GS = np.zeros(num_sim)
            GF = np.zeros(num_sim)
            CG = np.zeros(num_sim)
            SHO = np.zeros(num_sim)
            SV = np.zeros(num_sim)
            IP = np.zeros(num_sim)
            H = np.zeros(num_sim)
            R = np.zeros(num_sim)
            ER = np.zeros(num_sim)
            HR = np.zeros(num_sim)
            BB = np.zeros(num_sim)
            IBB = np.zeros(num_sim)
            SO = np.zeros(num_sim)
            HBP = np.zeros(num_sim)
            BK = np.zeros(num_sim)
            WP = np.zeros(num_sim)
            BF = np.zeros(num_sim)
            ERAplus = np.zeros(num_sim)
            FIP = np.zeros(num_sim)

        predictedW.append(W.mean())
        predictedL.append(L.mean())
        predictedG.append(G.mean())
        predictedGS.append(GS.mean())
        predictedGF.append(GF.mean())
        predictedCG.append(CG.mean())
        predictedSHO.append(SHO.mean())
        predictedSV.append(SV.mean())
        predictedIP.append(IP.mean())
        predictedH.append(H.mean())
        predictedR.append(R.mean())
        predictedER.append(ER.mean())
        predictedHR.append(HR.mean())
        predictedBB.append(BB.mean())
        predictedIBB.append(IBB.mean())
        predictedSO.append(SO.mean())
        predictedHBP.append(HBP.mean())
        predictedBK.append(BK.mean())
        predictedWP.append(WP.mean())
        predictedBF.append(BF.mean())
        predictedERAplus.append(ERAplus.mean())
        predictedFIP.append(FIP.mean())

    future['W'] = predictedW
    future['L'] = predictedL
    future['G'] = predictedG
    future['GS'] = predictedGS
    future['GF'] = predictedGF
    future['CG'] = predictedCG
    future['SHO'] = predictedSHO
    future['SV'] = predictedSV
    future['IP'] = predictedIP
    future['H'] = predictedH
    future['R'] = predictedR
    future['ER'] = predictedER
    future['HR'] = predictedHR
    future['BB'] = predictedBB
    future['IBB'] = predictedIBB
    future['SO'] = predictedSO
    future['HBP'] = predictedHBP
    future['BK'] = predictedBK
    future['WP'] = predictedWP
    future['BF'] = predictedBF
    future['ERA+'] = predictedERAplus
    future['FIP'] = predictedFIP

    future['ERA'] = 9*future['ER']/future['IP']
    future['WHIP'] = (future['H']+future['BB']+future['IBB']) / (future['IP'])
    future['H9'] = 9*future['H']/future['IP']
    future['BB9'] = 9*future['BB']/future['IP']
    future['HR9'] = 9*future['HR']/future['IP']
    future['SO9'] = 9*future['SO']/future['IP']
    future['SO-HR-BB/IP'] = (future['SO'] - future['HR'] - future['BB'])/future['IP']


    scale = future['GS'].apply(lambda x: min(1, 33 / x) if x > 0 else 1)
    #stats_cols = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'SO', 'OPS+', 'Rbat+', 'TB', 'GIDP', 'HBP', 'SH', 'SF', 'IBB']

    future[cols] = future[cols].multiply(scale, axis=0)

    future['W'] = future['W'].round(1)
    future['L'] = future['L'].round(1)
    future['G'] = future['G'].round(0)
    future['GS'] = future['GS'].round(0)
    future['GF'] = future['GF'].round(0)
    future['CG'] = future['CG'].round(0)
    future['SHO'] = future['SHO'].round(1)
    future['SV'] = future['SV'].round(1)
    future['IP'] = future['IP'].round(0)
    future['H'] = future['H'].round(1)
    future['R'] = future['R'].round(1)
    future['ER'] = future['ER'].round(1)
    future['HR'] = future['HR'].round(1)
    future['BB'] = future['BB'].round(1)
    future['IBB'] = future['IBB'].round(1)
    future['SO'] = future['SO'].round(1)
    future['HBP'] = future['HBP'].round(1)
    future['BK'] = future['BK'].round(1)
    future['WP'] = future['WP'].round(1)
    future['BF'] = future['BF'].round(1)
    future['ERA+'] = future['ERA+'].round(1)
    future['FIP'] = future['FIP'].round(3)

    future['ERA'] = future['ERA'].round(3)
    future['WHIP'] = future['WHIP'].round(3)
    future['H9'] = future['H9'].round(3)
    future['BB9'] = future['BB9'].round(3)
    future['HR9'] = future['HR9'].round(3)
    future['SO9'] = future['SO9'].round(3)
    future['SO-HR-BB/IP'] = future['SO-HR-BB/IP'].round(3)


    future['Rank'] = range(1, len(future) + 1)
    coles = ['Rank'] + [col for col in future.columns if col != 'Rank']
    future = future[coles]
    future = future.drop('PlayerID', axis=1) 
    future = future.drop('SO/BB', axis=1) 
    future = future.drop('W-L%', axis=1) 
    future[future.select_dtypes('number').columns] = future.select_dtypes('number').fillna(0)

    print(future.head(5))

    return future


def preseasonmlbpitchinghtml(future):

        html_string = future.to_html(classes='display', index=False).replace('class="dataframe display"', 'class="display"')

        # Full HTML file with sorting and ALL rows shown
        html_script = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title> Preseason Predictions </title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="icon" type="image/png" sizes="96x96" href="/WebProjects/images/favicon-96x96.png" />
        <link rel="icon" type="image/svg+xml" href="/WebProjects/images/favicon.svg" />
        <link rel="shortcut icon" href="/WebProjects/images/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/WebProjects/images/apple-touch-icon.png" />
        <meta name="apple-mobile-web-app-title" content="MyWebSit" />
        <link rel="manifest" href="/WebProjects/images/site.webmanifest" />

        <link rel="stylesheet" href="/WebProjects/style.css">


        </head>
        <body>

        <div class="topnav">
        <a href="/WebProjects/index.html">Home</a>
            <div class="dropdown">
            <button class="dropbtn">Football
                <i class="fa fa-caret-down"></i>
            </button>
            <div class="dropdown-content">
                <a href="/WebProjects/WeeklyPred_html/SuperFlex.html">Weekly Predictions</a>
                <a href="/WebProjects/ROS_html/Rest Of Season.html">Rest of Season Predictions</a>
                <a href="/WebProjects/WeeklyScores_html/Weekly Game Predictions.html">Weekly Game Predictions</a>
                <a href="/WebProjects/Dominance_html/QBDom.html">Offensive Focus</a>
            </div>
            </div>
            <div class="dropdown">
            <button class="dropbtn active">Baseball
                <i class="fa fa-caret-down"></i>
            </button>
            <div class="dropdown-content">
                <a href="/WebProjects/PreseasonMLBHittingPredictions.html">MLB Preseason Hitting Predictions</a>
                <a href="/WebProjects/PreseasonMLBPitchingPredictions.html">MLB Preseason Pitching Predictions</a>
            </div>
            </div>
        <a href="/WebProjects/Fitness_html/fitness.html">Fitness</a>
        <a href="/WebProjects/about.html">About</a>
        </div>
        

        <img src="/WebProjects/images/Banner_Logo.png" alt="Header Image" class="header-img">

        <h1>MLB Pitching Predictions</h1>

        <div class="topnav">
        <input type="text" id="searchBar" placeholder="Search...">
        </div>



        {html_string}

        <script>
        function getCellValue(row, index) {{
            return row.cells[index].textContent.trim();
        }}

        function comparer(index, asc) {{
            return function(a, b) {{
            const v1 = getCellValue(a, index);
            const v2 = getCellValue(b, index);

            const num1 = parseFloat(v1);
            const num2 = parseFloat(v2);
            const bothNumbers = !isNaN(num1) && !isNaN(num2);

            if (bothNumbers) {{
                return asc ? num1 - num2 : num2 - num1;
            }} else {{
                return asc ? v1.localeCompare(v2) : v2.localeCompare(v1);
            }}
            }};
        }}

        document.addEventListener("DOMContentLoaded", function () {{
            document.querySelectorAll("th").forEach(function (th, index) {{
            let ascending = true;
            if (index === 0) return;
            th.addEventListener("click", function () {{
                const table = th.closest("table");
                const tbody = table.querySelector("tbody");
                const rows = Array.from(tbody.querySelectorAll("tr"));
                rows.sort(comparer(index, ascending));
                //rows.forEach(row => tbody.appendChild(row));
                rows.forEach((row, i) => {{
                    row.cells[0].textContent = i + 1; // Reset Rank to match new row position
                    tbody.appendChild(row);
                }});
                ascending = !ascending;
            }});
            }});
        }});
        </script>

        

        <script>
        const searchBar = document.getElementById('searchBar');
        const table = document.querySelector('table');
        const rows = table.getElementsByTagName('tr');

        searchBar.addEventListener('keyup', function () {{
            const searchText = searchBar.value.toLowerCase();

            for (let i = 1; i < rows.length; i++) {{
            const row = rows[i];
            const rowText = row.textContent.toLowerCase();
            row.style.display = rowText.includes(searchText) ? '' : 'none';
            }}
        }});
        </script>

        

        </body>
        </html>
        """

        # Save to HTML file
        with open(f"PreseasonMLBPitchingPredictions.html", "w", encoding="utf-8") as f:
            f.write(html_script)


