import pandas as pd
import os
from collections import defaultdict
import numpy as np
import requests
from bs4 import BeautifulSoup
import time
import unicodedata
import random

#Age Regression
def age_adjust_projections1(row, curves):
    pos = row['Pos.']
    current_age = row['Age'] - 1
    target_age = row['Age']
    metrics = {'RushYds': 'Rush Y/A', 'RushTD': 'Rush TD/A', 'PassYds': 'Pass Y/A', 'PassTD': 'Pass TD/A', 'Int': 'INT/A', 'RecYds': 'Y/Rec', 'RecTD': 'Rec TD/Rec'}
    for projection_col, metric in metrics.items():
        if pos not in curves or metric not in curves[pos]:
            continue
        coef = curves[pos][metric]
        current_rate = np.polyval(coef, current_age)
        future_rate = np.polyval(coef, target_age)
        if not np.isfinite(current_rate) or not np.isfinite(future_rate) or current_rate <= 0 or future_rate <= 0:
            continue
        factor = future_rate / current_rate
        row[projection_col] *= factor
    row['Age'] = target_age
    return row


def age_adjust_projections(row, curves):
    pos = row['Pos.']
    current_age = row['Age'] - 1
    target_age = row['Age']
    metrics = {'RushYds': 'Rush Y/A', 'RushTD': 'Rush TD/A', 'PassYds': 'Pass Y/A', 'PassTD': 'Pass TD/A', 'Int': 'INT/A', 'RecYds': 'Y/Rec', 'RecTD': 'Rec TD/Rec'}
    aging_strengths = {'RushYds': 0.5, 'RushTD': 0.5, 'PassYds': 0.5, 'PassTD': 0.5, 'Int': 0.5, 'RecYds': 0.5, 'RecTD': 0.5}
    for projection_col, metric in metrics.items():
        if pos not in curves or metric not in curves[pos]:
            continue
        coef = curves[pos][metric]
        current_rate = np.polyval(coef, current_age)
        future_rate = np.polyval(coef, target_age)
        if not np.isfinite(current_rate) or not np.isfinite(future_rate) or current_rate <= 0 or future_rate <= 0:
            continue
        factor = (future_rate / current_rate) ** aging_strengths[projection_col]
        factor = np.clip(factor, 0.85, 1.15)
        row[projection_col] *= factor
    row['Age'] = target_age
    return row


def build_age_curves(Total_Stats):
    Total_Stats = Total_Stats.copy()
    age = Total_Stats['Age'].str.split('-', expand=True).astype(float)
    Total_Stats['Age'] = age[0] + round(age[1] / 365.25)
    age_pos = Total_Stats.groupby(['Age', 'Pos.']).mean(numeric_only=True).reset_index()
    Age_Curve = age_pos[['Age', 'Pos.']].copy()
    Age_Curve['Pass Y/A'] = age_pos['PassYds'] / age_pos['PassAtt']
    Age_Curve['Pass TD/A'] = age_pos['PassTD'] / age_pos['PassAtt']
    Age_Curve['INT/A'] = age_pos['Int'] / age_pos['PassAtt']
    Age_Curve['Rush Y/A'] = age_pos['RushYds'] / age_pos['RushAtt']
    Age_Curve['Rush TD/A'] = age_pos['RushTD'] / age_pos['RushAtt']
    Age_Curve['Y/Rec'] = age_pos['RecYds'] / age_pos['Rec']
    Age_Curve['Rec TD/Rec'] = age_pos['RecTD'] / age_pos['Rec']
    metrics = ['Rush Y/A', 'Pass Y/A', 'INT/A', 'Pass TD/A', 'Y/Rec', 'Rush TD/A', 'Rec TD/Rec']
    curves = {}
    for pos in Age_Curve['Pos.'].unique():
        curves[pos] = {}
        for metric in metrics:
            data = Age_Curve[Age_Curve['Pos.'] == pos][['Age', metric]].dropna()
            if len(data) >= 3:
                curves[pos][metric] = np.polyfit(data['Age'], data[metric], 2)
    return Age_Curve, curves


#NFL Scripts
def split_df_by_position(df, position_col="Pos."):
    dfs = {"All": df.copy()}

    for position in df[position_col].dropna().unique():
        dfs[position] = df[df[position_col] == position].copy()

    return dfs


def add_fantasy_points(df):
    """
    Add PPR and Standard fantasy points to a player stats DataFrame.

    Scoring:
        Passing:
            1 point per 25 passing yards
            4 points per passing TD
            -2 points per INT

        Rushing:
            1 point per 10 rushing yards
            6 points per rushing TD

        Receiving:
            1 point per 10 receiving yards
            6 points per receiving TD
            PPR: 1 point per reception
            Standard: 0 points per reception
    """

    ppr = (
        (df["PassYds"] / 25)
        + (df["PassTD"] * 4)
        - (df["Int"] * 2)
        + (df["RushYds"] / 10)
        + (df["RushTD"] * 6)
        + (df["RecYds"] / 10)
        + (df["RecTD"] * 6)
        + df["Rec"]
    )

    standard = (
        (df["PassYds"] / 25)
        + (df["PassTD"] * 4)
        - (df["Int"] * 2)
        + (df["RushYds"] / 10)
        + (df["RushTD"] * 6)
        + (df["RecYds"] / 10)
        + (df["RecTD"] * 6)
    )

    col_idx = df.columns.get_loc("Pos.")

    df.insert(col_idx + 1, "PPR", ppr)
    df.insert(col_idx + 2, "Std", standard)

    return df


def get_nfl_week_files(year, folder="CSVs"):
    files = []

    for filename in os.listdir(folder):
        if filename.startswith("Week_") and filename.endswith(f"_NFL_{year}.csv"):
            files.append(os.path.join(folder, filename))

    # Sort by week number
    files.sort(key=lambda x: int(os.path.basename(x).split("_")[1]))

    return files


def get_nfl_scores_files(year, folder="CSVs"):
    files = []

    for filename in os.listdir(folder):
        if filename.startswith("Week_") and filename.endswith(f"_Scores_{year}.csv"):
            files.append(os.path.join(folder, filename))

    # Sort by week number
    files.sort(key=lambda x: int(os.path.basename(x).split("_")[1]))

    return files


def importstats(csv): #imports CSV's via list and organizes them appropriately
    Dataframes=[]

    # Stats need to be from Stathead by sorted >0 snaps, pass attempts, rush attempts, targets
    
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

    # Get Schedule Grid from YEAR NFL Season Schedule Grid ESPN website
    # https://www.espn.com/nfl/schedulegrid
    
    # NFL Schedule
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
        player_pos = None

        total_ind_pass_att = 0  
        total_ind_pass_yards = 0
        total_ind_pass_td = 0
        total_ind_int = 0
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
        ind_total_int = 0
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
                player_pos = df.loc[df['Player'] == player, 'Pos.'].iloc[0]

                ind_total_PA = df.loc[df['Team'] == player_team, 'PassAtt'].sum()
                ind_total_PY = df.loc[df['Team'] == player_team, 'PassYds'].sum()
                ind_total_PT = df.loc[df['Team'] == player_team, 'PassTD'].sum()
                ind_total_int = df.loc[df['Team'] == player_team, 'Int'].sum()
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
                total_ind_int += ind_total_int
                total_ind_targets += ind_total_T
                total_ind_rec += ind_total_R
                total_ind_rec_yards += ind_total_RY
                total_ind_rec_td += ind_total_RT
                total_ind_rush_att += ind_total_Ru
                total_ind_rush_yards += ind_total_RuY
                total_ind_rush_td += ind_total_RuT

        # Save result
        totals.append({'Player': player, 'Pos.': player_pos, 'Team': player_team, 'TeamTotalPassAtt': total_ind_pass_att, 'TeamTotalPassYds': total_ind_pass_yards, 'TeamTotalPassTD': total_ind_pass_td, 'TeamTotalInt': total_ind_int, 'TeamTotalTgt': total_ind_targets , 'TeamTotalRec': total_ind_rec, 'TeamTotalRecYds': total_ind_rec_yards, 'TeamTotalRecTD': total_ind_rec_td, 'TeamTotalRushAtt': total_ind_rush_att, 'TeamTotalRushYds': total_ind_rush_yards, 'TeamTotalRushTD': total_ind_rush_td})
    

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
    Usefulcolumns = ['Player', 'Team', 'Opp', 'Week', 'Pos.', 'G', 'PassAtt', 'PassAttStDev', 'Cmp', 'IndComp%', 'CompStDev', 'TeamComp%', 'PassYds', 'PassYdsStDev', 'PassYds%', 'PassTD', 'PassTDStDev', 'PassTD%', 'Int', 'IntStDev', 'Int%', 'Tgt', 'TgtStDev','Rec', 'IndCatch%', 'CatStDev', 'TmCatch%', 'RecYds', 'RecYdsStDev', 'RecYds%', 'RecTD', 'RecTDStDev', 'RecTD%', 'RushAtt', 'RushStDev', 'Rush%', 'RushYds', 'RushYdsStDev', 'RushYds%', 'RushTD', 'RushTDStDev', 'RushTD%', ]
    Useful = pd.DataFrame(columns=Usefulcolumns)

    # Pre-map Opponents for quick lookup
    week = min(week, 18)
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
                'Int': 'IntStDev',
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

        # Update Team Int Percentage
    Useful['Int%'] = np.where(
        individualtotals['TeamTotalInt'] != 0, (Useful['Int'] / individualtotals['TeamTotalInt']), 0)
    Useful['Int%'] = Useful['Int%'].fillna(0)

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
    

def build_depth_chart(df, year, output_dir='CSVs'):
    df = df.copy()
    df['Depth'] = pd.NA
    df['RBUsage%'] = df['Rush%'] + df['TmCatch%']
    rank_metrics = {'QB': 'PassYds%', 'WR': 'TmCatch%', 'TE': 'TmCatch%', 'RB': 'RBUsage%'}
    for pos, metric in rank_metrics.items():
        mask = df['Pos.'] == pos
        ranked = df.loc[mask].sort_values(['Team', metric], ascending=[True, False]).groupby('Team').cumcount().add(1)
        df.loc[ranked.index, 'Depth'] = ranked.astype(int)
    df = df.sort_values(['Team', 'Pos.', 'Depth', 'Player'])
    filename = f'{output_dir}/depth_chart_{year}.csv'
    df.to_csv(filename, index=False)
    print(f'Depth chart saved to {filename}')
    return df


def get_preseason_rosters(year): 
    """ Pull QB, RB, WR, and TE rosters for all 32 NFL teams from ESPN's public JSON API. 
    Parameters ---------- year : int or str Used to label the output CSV. 
    Returns ------- pandas.DataFrame DataFrame containing all skill-position players. 
    """ 
    teams = [ "ari", "atl", "bal", "buf", 
             "car", "chi", "cin", "cle", 
             "dal", "den", "det", "gb", 
             "hou", "ind", "jax", "kc", 
             "lv", "lac", "lar", "mia", 
             "min", "ne", "no", "nyg", 
             "nyj", "phi", "pit", "sf", 
             "sea", "tb", "ten", "wsh" ] 

    
    all_players = [] 
    headers = { "User-Agent": "Mozilla/5.0" } 


    for team in teams: 
        url = ( f"https://site.api.espn.com/apis/site/v2/" f"sports/football/nfl/teams/{team}" f"?enable=roster" ) 
        try: 
            response = requests.get( url, headers=headers, timeout=15 ) 
            response.raise_for_status() 
            data = response.json() 
            team_data = data.get("team", {})
            athletes = team_data.get("athletes", [])

            if not athletes: 
                for group in team_data.get("groups", []): 
                    athletes.extend(group.get("athletes", []))

            for player in athletes: 
                position = player.get("position", {}) 

                if isinstance(position, dict): 
                    pos = position.get("abbreviation") 

                else: 
                    pos = position 

                if pos not in ["QB", "RB", "WR", "TE"]: 
                    continue 

                experience = player.get("experience", {}) 

                if isinstance(experience, dict): 
                    exp = experience.get("years") 

                else: 
                    exp = experience 
                college = player.get("college", {}) 

                if isinstance(college, dict): 
                    college_name = college.get("name") 

                else: 
                    college_name = college 

                all_players.append({ "Team": team.upper(), "Player": player.get("fullName"), "Pos.": pos, "Age": player.get("age"), "HT": player.get("displayHeight"), "WT": player.get("displayWeight"), "Exp": exp, "College": college_name }) 
            
            time.sleep(random.uniform(5, 15))

        except Exception as e: 
            print(f"Missed {team}: {e}")
            time.sleep(random.uniform(5, 15))
            continue 

    if not all_players: 
        raise RuntimeError("No roster data was returned from ESPN.") 
    
    roster_df = pd.DataFrame(all_players) 
    roster_df = roster_df[ ["Team", "Player", "Pos.", "Age", "HT", "WT", "Exp", "College"] ] 
    roster_df = roster_df.sort_values( ["Team", "Pos.", "Player"] ).reset_index(drop=True) 

    filename = f"CSVs/nfl_skill_players_{year}.csv" 
    roster_df.to_csv(filename, index=False) 

    print("Preseason Rosters completed") 
    
    return roster_df


def get_nfl_draft(year):
    """
    Pull QB, RB, WR, and TE selections from the specified NFL Draft
    using ESPN's API.

    Parameters
    ----------
    year : int or str
        NFL Draft year.

    Returns
    -------
    pandas.DataFrame
        Drafted QB, RB, WR, and TE players.
    """

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    rounds_url = (
        f"https://sports.core.api.espn.com/v2/"
        f"sports/football/leagues/nfl/seasons/{year}/draft/rounds"
    )

    response = requests.get(
        rounds_url,
        headers=headers,
        timeout=20
    )
    response.raise_for_status()

    rounds_data = response.json()

    results = []

    for draft_round in rounds_data.get("items", []):

        round_number = draft_round.get("number")

        for pick in draft_round.get("picks", []):

            athlete = pick.get("athlete", {})

            # ESPN sometimes returns an athlete as a $ref
            athlete_url = athlete.get("$ref")

            if not athlete_url:
                continue

            # Convert ESPN's http reference to https
            athlete_url = athlete_url.replace(
                "http://",
                "https://"
            )

            try:
                player_response = requests.get(
                    athlete_url,
                    headers=headers,
                    timeout=20
                )

                player_response.raise_for_status()

                player = player_response.json()

            except requests.RequestException:
                continue

            position = player.get("position", {})

            if isinstance(position, dict):
                position_name = position.get("abbreviation")
            else:
                position_name = position

            # Only keep QB, RB, WR, TE
            if position_name not in ["QB", "RB", "WR", "TE"]:
                continue

            college = player.get("college", {})

            if isinstance(college, dict):
                school = college.get("name")
            else:
                school = college

            results.append({
                "Draft_Year": year,
                "Round": round_number,
                "Player": player.get("fullName"),
                "School": school,
                "Position": position_name
            })

    if not results:
        raise RuntimeError(
            f"No NFL draft data was returned for {year}."
        )

    df = pd.DataFrame(results)

    df = df.drop_duplicates()

    df = df[
        [
            "Draft_Year",
            "Round",
            "Player",
            "School",
            "Position"
        ]
    ]

    filename = f"CSVs/nfl_draft_{year}.csv"

    df.to_csv(
        filename,
        index=False
    )

    print("NFL Draft completed")

    return df


def standardize_player_names(df):

    name_fixes = {
        "Michael Penix Jr.": "Michael Penix",
        "Bam Knight": "Zonovan Knight",
        "James Cook III": "James Cook",
        "DJ Moore": "D.J. Moore",
        "Joshua Palmer": "Josh Palmer",
        "Mecole Hardman Jr.": "Mecole Hardman",
        "Luther Burden III": "Luther Burden",
        "Harold Fannin Jr.": "Harold Fannin",
        "Joe Milton III": "Joe Milton",
        "Anthony Richardson Sr.": "Anthony Richardson",
        "Chris Rodriguez Jr.": "Chris Rodriguez",
        "Brian Thomas Jr.": "Brian Thomas",
        "Stetson Bennett IV": "Stetson Bennett",
        "Phillip Dorsett II": "Phillip Dorsett",
        "Ollie Gordon II": "Ollie Gordon",
        "Aaron Jones Sr.": "Aaron Jones",
        "Travis Etienne Jr.": "Travis Etienne",
        "Hollywood Brown": "Marquise Brown",
        "DK Metcalf": "D.K. Metcalf",
        "Deebo Samuel Sr.": "Deebo Samuel",
        "Chris Godwin Jr.": "Chris Godwin",
        "Kyle Pitts Sr.": "Kyle Pitts",
        "Kenny Gainwell": "Kenneth Gainwell",
        "Oronde Gadsden Jr.": "Oronde Gadsden"
    }
    df["Player"] = (df["Player"].replace(name_fixes)
    )

    return df


def update_depth_chart1(previous_depth, new_roster, off_focus_df, draft_df): #Has ability to change depth chart manually
    """
    Update depth chart after offseason roster changes.

    Ranking priority:
    1. Previous depth number (lower is better)
    2. Off Focus (higher is better)
    3. Usage metric:
       - PassYds% for QB
       - TmCatch% for WR/TE
       - Rush% for RB

    Draft prospects receive an Off Focus score based on
    their draft round and position.

    Parameters
    ----------
    previous_depth : DataFrame
        Prior depth chart containing:
        Player, Team, Pos., Depth, TmCatch%, Rush%, PassYds%

    new_roster : DataFrame
        New roster containing:
        Player, Team, Pos.

    off_focus_df : DataFrame
        Player evaluation containing:
        Player, Off Focus

    draft_df : DataFrame
        Draft data containing:
        Player, Round, Position

    Returns
    -------
    DataFrame
        Updated depth chart
    """

    off_focus_df = standardize_player_names(off_focus_df)
    new_roster = standardize_player_names(new_roster)
    previous_depth = standardize_player_names(previous_depth)

    df = new_roster.copy()

    # ---------------------------------------------------------
    # Bring previous player information forward
    # ---------------------------------------------------------


    df = df.merge(
        previous_depth[
            ["Player", "Pos.", "Depth", "TmCatch%", "Rush%", "PassYds%"]
        ],
        on=["Player", "Pos."],
        how="left"
    )

    df = df.rename(columns={"Depth": "PrevDepth"})

    # Players without a previous depth go last
    df["PrevDepth"] = pd.to_numeric(df["PrevDepth"], errors="coerce").fillna(99)

    # ---------------------------------------------------------
    # Add existing offensive focus
    # ---------------------------------------------------------

    df = df.merge(
        off_focus_df[["Player", "Off Focus"]],
        on="Player",
        how="left"
    )

    # ---------------------------------------------------------
    # Add draft-round offensive focus
    # ---------------------------------------------------------

    draft_off_focus = {
        "QB": {
            1: 10,
            2: 9,
            3: 7,
            4: 5,
            5: 3,
            6: 1,
            7: 0
        },
        "WR": {
            1: 85,
            2: 60,
            3: 40,
            4: 10,
            5: 5,
            6: 0,
            7: 0
        },
        "TE": {
            1: 65,
            2: 50,
            3: 35,
            4: 20,
            5: 10,
            6: 5,
            7: 0
        },
        "RB": {
            1: 200,
            2: 150,
            3: 125,
            4: 100,
            5: 75,
            6: 50,
            7: 25
        }
    }

    draft_info = draft_df[
        ["Player", "Round", "Position"]
    ].copy()

    draft_info["Draft Off Focus"] = draft_info.apply(
        lambda row: draft_off_focus
            .get(row["Position"], {})
            .get(row["Round"], 0),
        axis=1
    )

    # Add draft information to roster
    df = df.merge(
        draft_info[
            ["Player", "Round", "Position", "Draft Off Focus"]
        ],
        on="Player",
        how="left"
    )

    # Use existing Off Focus if one exists.
    # Otherwise use the draft-based Off Focus.
    df.loc[
        df["Off Focus"].isna(),
        "Off Focus"
    ] = df.loc[
        df["Off Focus"].isna(),
        "Draft Off Focus"
    ]

    # Players with neither an existing Off Focus
    # nor a draft score receive 0
    df["Off Focus"] = pd.to_numeric(df["Off Focus"], errors="coerce").fillna(0)

    # ---------------------------------------------------------
    # Rank each position
    # ---------------------------------------------------------

    results = []

    for pos, metric in {
        "QB": "PassYds%",
        "WR": "TmCatch%",
        "TE": "TmCatch%",
        "RB": "Rush%"
    }.items():

        temp = df[df["Pos."] == pos].copy()

        # New players with no history have no usage metric
        temp[metric] = temp[metric].fillna(0)

        temp = temp.sort_values(
            ["Team", "Off Focus", "PrevDepth", metric],
            ascending=[True, False, True, False]
        )

        temp["Depth"] = (
            temp.groupby("Team")
                .cumcount()
                .add(1)
        )

        results.append(temp)

    # ---------------------------------------------------------
    # Combine and clean
    # ---------------------------------------------------------

    final_depth_chart = pd.concat(results).sort_values(["Team", "Pos.", "Depth"]).reset_index(drop=True)

        # Manually Override some players Depth
    manual_depth = {
        "Joe Flacco": 2,
        "Joe Burrow": 1,
        "Davis Mills": 2,
        "C.J. Stroud": 1,
        "Justin Fields": 2,
        "Patrick Mahomes": 1,
        "Carson Wentz": 3,
        "Kyler Murray": 1,
        "J.J. McCarthy": 2,
        "Justin Jefferson": 1,
        "Jauan Jennings": 2,
        "Jordan Addison": 3,
        "Jameis Winston": 2,
        "Jaxson Dart": 1,
        "Kyle Pitts": 1,
        "Tyson Bagent": 2,
        "Caleb Williams": 1,
        "Cam Ward": 1,
        "Mitchell Trubisky": 2,
        "Cyrus Allen": 3,
        "Tyquan Thornton": 4,
        "DeVonta Smith": 1,
        "Makai Lemon": 2,
        "Dontayvion Wicks": 3,
        "Kenneth Gainwell": 2,
        "Sean Tucker": 3,
        "Jeremiyah Love": 1,
        "Tyler Allgeier": 2,
        "James Conner": 4,
        "Zonovan Knight": 3,
        "Jonathon Brooks": 2,
        "AJ Dillon": 3,
        "Trevor Etienne": 4,
        "Anthony Tyus III": 5,
        "Deshaun Watson": 1,
        "Dillon Gabriel": 3,
        "Keaton Mitchell": 3,
        "Jaret Patterson": 4,
        "Terrance Ferguson": 1,
        "Max Klare": 4,
        "Rashid Shaheed": 2,
        "Tory Horton": 4,
        "Tyjae Spears": 2,
        "Nicholas Singleton": 3,
        "Michael Carter": 4 
    }

    final_depth_chart["Depth"] = final_depth_chart["Player"].map(manual_depth).fillna(final_depth_chart["Depth"])

    final_depth_chart["Depth"] = final_depth_chart["Depth"].astype(int)

    final_depth_chart = final_depth_chart.sort_values(
        ["Team", "Pos.", "Depth"]
    ).reset_index(drop=True)

    return final_depth_chart





    for df in [df1, df2, df3, df4]:
        df["Team"] = df["Team"].astype(str).str.replace("\xa0", " ", regex=False).str.strip()
        df["Pos."] = df["Pos."].astype(str).str.replace("\xa0", " ", regex=False).str.strip()


    stats = [
        "PassYds", "PassTD", "Rec", "RecYds", "RecTD",
        "RushAtt", "RushYds", "RushTD"
    ]

    # ---------------------------------------------------------
    # Clean numeric columns
    # ---------------------------------------------------------
    for df in [df1, df2, df3, df4]:
        cols = df.select_dtypes(include="number").columns
        df[cols] = (
            df[cols]
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
            .round()
            .astype(int)
        )

    # ---------------------------------------------------------
    # 1. Get Team + Position totals
    #
    # df1 = last year's totals
    # df2 = current projected totals
    # ---------------------------------------------------------
    df1_totals = (
        df1.groupby(["Team", "Pos."])[stats]
        .sum()
        .reset_index()
    )

    df2_totals = (
        df2.groupby(["Team", "Pos."])[stats]
        .sum()
        .reset_index()
    )

    # ---------------------------------------------------------
    # 2. Historical - projected = remaining
    # ---------------------------------------------------------
    remaining = df1_totals.merge(
        df2_totals,
        on=["Team", "Pos."],
        how="left",
        suffixes=("_last", "_projected")
    )

    for stat in stats:
        remaining[stat] = (
            remaining[f"{stat}_last"].fillna(0)
            - remaining[f"{stat}_projected"].fillna(0)
        )

    # ---------------------------------------------------------
    # Historical Team + Position distribution
    # Used to determine allocation percentages by Depth
    # ---------------------------------------------------------
    historical_dist = (
        df1.groupby(["Team", "Pos."])[stats]
        .sum()
        .reset_index()
    )

    # ---------------------------------------------------------
    # 3. Allocate stats from players who left the team
    #
    # df4 = historical player stats
    # df3 = current player stats
    #
    # Historical distribution determines the weights.
    # Those weights are assigned in order to current players
    # by Depth.
    # ---------------------------------------------------------
    for team in df3["Team"].unique():

        for pos in df3["Pos."].unique():

            players = (
                df3[
                    (df3["Team"] == team) &
                    (df3["Pos."] == pos)
                ]
                .sort_values("Depth")
            )

            if players.empty:
                continue

            historical = df4[
                (df4["Team"] == team) &
                (df4["Pos."] == pos)
            ].copy()

            if historical.empty:
                continue

            current_names = set(players["Player"])

            # Players who left the team
            departed = historical[
                ~historical["Player"].isin(current_names)
            ]

            if departed.empty:
                continue

            for stat in stats:

                # Stats lost from departed players
                lost_amount = int(departed[stat].sum())

                if lost_amount <= 0:
                    continue

                # -------------------------------------------------
                # Historical player distribution
                #
                # Rank historical players by their share of the
                # team's production.
                # -------------------------------------------------
                historical_player_totals = (
                    historical
                    .groupby("Player")[stat]
                    .sum()
                    .sort_values(ascending=False)
                )

                historical_total = historical_player_totals.sum()

                if historical_total <= 0:
                    continue

                historical_pct = (
                    historical_player_totals / historical_total
                )

                # -------------------------------------------------
                # Apply historical distribution by ORDER to
                # current players by Depth.
                #
                # Historical #1 -> Depth 1
                # Historical #2 -> Depth 2
                # Historical #3 -> Depth 3
                # etc.
                # -------------------------------------------------
                for i, idx in enumerate(players.index):

                    if i >= len(historical_pct):
                        break

                    pct = historical_pct.iloc[i]

                    change = int(round(lost_amount * pct))

                    df3.loc[idx, stat] += change



    print("AFTER SECTION 3 - Stafford")
    print(
        df3[
            (df3["Player"] == "Matthew Stafford") &
            (df3["Team"] == "LAR")
        ][["Player", "Team", "Depth", "PassYds", "PassTD"]]
    )



    # ---------------------------------------------------------
    # Redistribute ALL Depth 3 QB stats to Depth 1 and 2
    # ---------------------------------------------------------
    for team in df3["Team"].unique():

        qbs = (
            df3[
                (df3["Team"] == team) &
                (df3["Pos."] == "QB")
            ]
            .sort_values("Depth")
        )

        if len(qbs) < 3:
            continue

        qb1 = qbs.iloc[0].name
        qb2 = qbs.iloc[1].name
        qb3 = qbs.iloc[2].name

        for stat in stats:

            depth3_value = int(df3.loc[qb3, stat])

            if depth3_value == 0:
                continue

            # Remove everything from QB3
            df3.loc[qb3, stat] = 0

            # Split between QB1 and QB2
            base = depth3_value // 2
            remainder = depth3_value % 2

            df3.loc[qb1, stat] += base + remainder
            df3.loc[qb2, stat] += base


    # ---------------------------------------------------------
    # Historical receiving-yard distribution by team
    # df1 = previous year's actual stats
    # ---------------------------------------------------------
    receiving_dist = (
        df1[df1["Pos."].isin(["WR", "RB", "TE"])]
        .groupby(["Team", "Pos."])["RecYds"]
        .sum()
        .unstack(fill_value=0)
    )

    for pos in ["WR", "RB", "TE"]:
        if pos not in receiving_dist.columns:
            receiving_dist[pos] = 0

    receiving_dist["TotalRecYds"] = (
        receiving_dist["WR"] +
        receiving_dist["RB"] +
        receiving_dist["TE"]
    )

    for pos in ["WR", "RB", "TE"]:
        receiving_dist[f"{pos}_pct"] = (
            receiving_dist[pos] /
            receiving_dist["TotalRecYds"]
        ).fillna(0)

    # ---------------------------------------------------------
    # Historical receiving-TD distribution by team
    # df1 = previous year's actual stats
    # ---------------------------------------------------------
    receiving_td_dist = (
        df1[df1["Pos."].isin(["WR", "RB", "TE"])]
        .groupby(["Team", "Pos."])["RecTD"]
        .sum()
        .unstack(fill_value=0)
    )

    for pos in ["WR", "RB", "TE"]:
        if pos not in receiving_td_dist.columns:
            receiving_td_dist[pos] = 0

    receiving_td_dist["TotalRecTD"] = (
        receiving_td_dist["WR"] +
        receiving_td_dist["RB"] +
        receiving_td_dist["TE"]
    )

    for pos in ["WR", "RB", "TE"]:
        receiving_td_dist[f"{pos}_pct"] = (
            receiving_td_dist[pos] /
            receiving_td_dist["TotalRecTD"]
        ).fillna(0)

    print("AFTER QB3 REDISTRIBUTION - Stafford")
    print(
        df3[
            (df3["Player"] == "Matthew Stafford") &
            (df3["Team"] == "LAR")
        ][["Player", "Team", "Depth", "PassYds", "PassTD"]]
    )


    # ---------------------------------------------------------
    # 4. Reconcile Passing vs Receiving at the TEAM level
    #
    # Passing yards should equal receiving yards
    # Passing TDs should equal receiving TDs
    # ---------------------------------------------------------
    for team in df3["Team"].unique():

        team_mask = df3["Team"] == team

        pass_yds = df3.loc[team_mask, "PassYds"].sum()
        rec_yds = df3.loc[team_mask, "RecYds"].sum()

        pass_td = df3.loc[team_mask, "PassTD"].sum()
        rec_td = df3.loc[team_mask, "RecTD"].sum()

        # -----------------------------------------------------
        # Receiving yards adjustment
        # -----------------------------------------------------
        if pass_yds > rec_yds:
           # df3.loc[team_mask, "PassYds"] -= int(pass_yds - rec_yds)
                pass_yd_diff = int(pass_yds - rec_yds)

                qbs = (
                    df3[
                        (df3["Team"] == team) &
                        (df3["Pos."] == "QB")
                    ]
                    .sort_values("Depth")
                    .head(2)
                )

                if not qbs.empty:

                    base = pass_yd_diff // len(qbs)
                    remainder = pass_yd_diff % len(qbs)

                    for i, idx in enumerate(qbs.index):

                        change = base + (1 if i < remainder else 0)

                        df3.loc[idx, "PassYds"] -= change
        
        elif rec_yds > pass_yds:
            rec_yd_diff = int(rec_yds - pass_yds)

            # Get this team's previous-year receiving-yard distribution
            if team in receiving_dist.index:
                wr_pct = receiving_dist.loc[team, "WR_pct"]
                rb_pct = receiving_dist.loc[team, "RB_pct"]
                te_pct = receiving_dist.loc[team, "TE_pct"]
            else:
                wr_pct = 0
                rb_pct = 0
                te_pct = 0
            
            wrs = (
                df3[
                    (df3["Team"] == team) &
                    (df3["Pos."] == "WR")
                ]
                .sort_values("Depth")
                .head(3)
            )

            rbs = (
                df3[
                    (df3["Team"] == team) &
                    (df3["Pos."] == "RB")
                ]
                .sort_values("Depth")
                .head(3)
            )

            tes = (
                df3[
                    (df3["Team"] == team) &
                    (df3["Pos."] == "TE")
                ]
                .sort_values("Depth")
                .head(3)
            )

            # -----------------------------------------------------
            # Allocate correction using previous year's
            # receiving-yard distribution
            # -----------------------------------------------------
            if not wrs.empty and not rbs.empty and not tes.empty:

                wr_amount = int(round(rec_yd_diff * wr_pct))
                rb_amount = int(round(rec_yd_diff * rb_pct))

                # TE gets the remainder so the correction is exact
                te_amount = rec_yd_diff - wr_amount - rb_amount

            elif not wrs.empty and not rbs.empty:

                wr_amount = int(round(rec_yd_diff * wr_pct))
                rb_amount = rec_yd_diff - wr_amount
                te_amount = 0

            elif not wrs.empty and not tes.empty:

                wr_amount = int(round(rec_yd_diff * wr_pct))
                te_amount = rec_yd_diff - wr_amount
                rb_amount = 0

            elif not rbs.empty and not tes.empty:

                rb_amount = int(round(rec_yd_diff * rb_pct))
                te_amount = rec_yd_diff - rb_amount
                wr_amount = 0

            elif not wrs.empty:

                wr_amount = rec_yd_diff
                rb_amount = 0
                te_amount = 0

            elif not rbs.empty:

                wr_amount = 0
                rb_amount = rec_yd_diff
                te_amount = 0

            elif not tes.empty:

                wr_amount = 0
                rb_amount = 0
                te_amount = rec_yd_diff

            else:

                wr_amount = 0
                rb_amount = 0
                te_amount = 0

            # Distribute WR portion
            if not wrs.empty and wr_amount != 0:

                base = abs(wr_amount) // len(wrs)
                remainder = abs(wr_amount) % len(wrs)

                for i, idx in enumerate(wrs.index):

                    change = base + (1 if i < remainder else 0)

                    if wr_amount < 0:
                        change = -change

                    df3.loc[idx, "RecYds"] -= change

            # Distribute RB portion
            if not rbs.empty and rb_amount != 0:

                base = abs(rb_amount) // len(rbs)
                remainder = abs(rb_amount) % len(rbs)

                for i, idx in enumerate(rbs.index):

                    change = base + (1 if i < remainder else 0)

                    if rb_amount < 0:
                        change = -change

                    df3.loc[idx, "RecYds"] -= change
                    
            # Distribute TE portion
            if not tes.empty and te_amount != 0:

                base = abs(te_amount) // len(tes)
                remainder = abs(te_amount) % len(tes)

                for i, idx in enumerate(tes.index):

                    change = base + (1 if i < remainder else 0)

                    if te_amount < 0:
                        change = -change

                    df3.loc[idx, "RecYds"] -= change
                    
        pass_yds_after = df3.loc[team_mask, "PassYds"].sum()
        rec_yds_after = df3.loc[team_mask, "RecYds"].sum()

        # -----------------------------------------------------
        # Receiving TD adjustment
        # -----------------------------------------------------
        if pass_td > rec_td:

            pass_td_diff = int(pass_td - rec_td)

            qbs = (
                df3[
                    (df3["Team"] == team) &
                    (df3["Pos."] == "QB")
                ]
                .sort_values("Depth")
                .head(2)
            )

            if not qbs.empty:

                base = pass_td_diff // len(qbs)
                remainder = pass_td_diff % len(qbs)

                for i, idx in enumerate(qbs.index):

                    change = base + (1 if i < remainder else 0)

                    df3.loc[idx, "PassTD"] -= change
        
        elif rec_td > pass_td:

            rec_td_diff = int(rec_td - pass_td)

            # -------------------------------------------------
            # Get this team's previous-year receiving TD
            # distribution
            # -------------------------------------------------
            if team in receiving_td_dist.index:

                wr_pct = receiving_td_dist.loc[team, "WR_pct"]
                rb_pct = receiving_td_dist.loc[team, "RB_pct"]
                te_pct = receiving_td_dist.loc[team, "TE_pct"]

            else:

                wr_pct = 0
                rb_pct = 0
                te_pct = 0

            # -------------------------------------------------
            # Get top 3 WRs
            # -------------------------------------------------
            wrs = (
                df3[
                    (df3["Team"] == team) &
                    (df3["Pos."] == "WR")
                ]
                .sort_values("Depth")
                .head(3)
            )

            # -------------------------------------------------
            # Get top 3 RBs
            # -------------------------------------------------
            rbs = (
                df3[
                    (df3["Team"] == team) &
                    (df3["Pos."] == "RB")
                ]
                .sort_values("Depth")
                .head(3)
            )

            # -------------------------------------------------
            # Get top 3 TEs
            # -------------------------------------------------
            tes = (
                df3[
                    (df3["Team"] == team) &
                    (df3["Pos."] == "TE")
                ]
                .sort_values("Depth")
                .head(3)
            )

            # -------------------------------------------------
            # Allocate correction using previous year's
            # receiving-TD distribution
            # -------------------------------------------------
            if not wrs.empty and not rbs.empty and not tes.empty:

                wr_amount = int(round(rec_td_diff * wr_pct))
                rb_amount = int(round(rec_td_diff * rb_pct))

                # TE gets remainder so correction is exact
                te_amount = rec_td_diff - wr_amount - rb_amount

            elif not wrs.empty and not rbs.empty:

                wr_amount = int(round(rec_td_diff * wr_pct))
                rb_amount = rec_td_diff - wr_amount
                te_amount = 0

            elif not wrs.empty and not tes.empty:

                wr_amount = int(round(rec_td_diff * wr_pct))
                te_amount = rec_td_diff - wr_amount
                rb_amount = 0

            elif not rbs.empty and not tes.empty:

                rb_amount = int(round(rec_td_diff * rb_pct))
                te_amount = rec_td_diff - rb_amount
                wr_amount = 0

            elif not wrs.empty:

                wr_amount = rec_td_diff
                rb_amount = 0
                te_amount = 0

            elif not rbs.empty:

                wr_amount = 0
                rb_amount = rec_td_diff
                te_amount = 0

            elif not tes.empty:

                wr_amount = 0
                rb_amount = 0
                te_amount = rec_td_diff

            else:

                wr_amount = 0
                rb_amount = 0
                te_amount = 0

            # -------------------------------------------------
            # Reduce WR receiving TDs
            # -------------------------------------------------
            if not wrs.empty and wr_amount != 0:

                base = wr_amount // len(wrs)
                remainder = wr_amount % len(wrs)

                for i, idx in enumerate(wrs.index):

                    change = base + (1 if i < remainder else 0)

                    df3.loc[idx, "RecTD"] -= change

            # -------------------------------------------------
            # Reduce RB receiving TDs
            # -------------------------------------------------
            if not rbs.empty and rb_amount != 0:

                base = rb_amount // len(rbs)
                remainder = rb_amount % len(rbs)

                for i, idx in enumerate(rbs.index):

                    change = base + (1 if i < remainder else 0)

                    df3.loc[idx, "RecTD"] -= change

            # -------------------------------------------------
            # Reduce TE receiving TDs
            # -------------------------------------------------
            if not tes.empty and te_amount != 0:

                base = te_amount // len(tes)
                remainder = te_amount % len(tes)

                for i, idx in enumerate(tes.index):

                    change = base + (1 if i < remainder else 0)

                    df3.loc[idx, "RecTD"] -= change

    print("AFTER RECONCILIATION - Stafford")
    print(
        df3[
            (df3["Player"] == "Matthew Stafford") &
            (df3["Team"] == "LAR")
        ][["Player", "Team", "Depth", "PassYds", "PassTD"]]
    )


    return df3


def update_depth_chart(previous_depth, new_roster, off_focus_df, draft_df):
    off_focus_df = standardize_player_names(off_focus_df)
    new_roster = standardize_player_names(new_roster)
    previous_depth = standardize_player_names(previous_depth)
    df = new_roster.copy()
    df = df.merge(previous_depth[['Player', 'Pos.', 'Depth', 'TmCatch%', 'Rush%', 'PassYds%']], on=['Player', 'Pos.'], how='left')
    df = df.rename(columns={'Depth': 'PrevDepth'})
    df['PrevDepth'] = pd.to_numeric(df['PrevDepth'], errors='coerce').fillna(99)
    df = df.merge(off_focus_df[['Player', 'Off Focus']], on='Player', how='left')
    draft_off_focus = {'QB': {1: 10, 2: 9, 3: 7, 4: 5, 5: 3, 6: 1, 7: 0}, 'WR': {1: 85, 2: 60, 3: 40, 4: 10, 5: 5, 6: 0, 7: 0}, 'TE': {1: 65, 2: 50, 3: 35, 4: 20, 5: 10, 6: 5, 7: 0}, 'RB': {1: 200, 2: 150, 3: 125, 4: 100, 5: 75, 6: 50, 7: 25}}
    draft_info = draft_df[['Player', 'Round', 'Position']].copy()
    draft_info['Draft Off Focus'] = draft_info.apply(lambda row: draft_off_focus.get(row['Position'], {}).get(row['Round'], 0), axis=1)
    df = df.merge(draft_info[['Player', 'Round', 'Position', 'Draft Off Focus']], on='Player', how='left')
    df.loc[df['Off Focus'].isna(), 'Off Focus'] = df.loc[df['Off Focus'].isna(), 'Draft Off Focus']
    df['Off Focus'] = pd.to_numeric(df['Off Focus'], errors='coerce').fillna(0)
    df['RBUsage%'] = df['Rush%'].fillna(0) + df['TmCatch%'].fillna(0)
    results = []
    for pos, metric in {'QB': 'PassYds%', 'WR': 'TmCatch%', 'TE': 'TmCatch%', 'RB': 'RBUsage%'}.items():
        temp = df[df['Pos.'] == pos].copy()
        temp[metric] = temp[metric].fillna(0)
        temp = temp.sort_values(['Team', 'Off Focus', 'PrevDepth', metric], ascending=[True, False, True, False])
        temp['Depth'] = temp.groupby('Team').cumcount().add(1)
        results.append(temp)
    final_depth_chart = pd.concat(results).sort_values(['Team', 'Pos.', 'Depth']).reset_index(drop=True)
    return final_depth_chart


def apply_manual_depth_overrides(df):
    df = df.copy()
    manual_depth = {'Joe Flacco': 2, 
                    'Joe Burrow': 1, 
                    'Davis Mills': 2, 
                    'C.J. Stroud': 1, 
                    'Justin Fields': 2, 
                    'Patrick Mahomes': 1, 
                    'Carson Wentz': 3, 
                    'Kyler Murray': 1, 
                    'J.J. McCarthy': 2, 
                    'Justin Jefferson': 1, 
                    'Jauan Jennings': 2, 
                    'Jordan Addison': 3, 
                    'Jameis Winston': 2, 
                    'Jaxson Dart': 1, 
                    'Kyle Pitts': 1, 
                    'Tyson Bagent': 2, 
                    'Caleb Williams': 1, 
                    'Cam Ward': 1, 
                    'Mitchell Trubisky': 2, 
                    'Cyrus Allen': 3, 
                    'Tyquan Thornton': 4, 
                    'DeVonta Smith': 1, 
                    'Makai Lemon': 2, 
                    'Dontayvion Wicks': 3, 
                    'Kenneth Gainwell': 2, 
                    'Sean Tucker': 3, 
                    'Jeremiyah Love': 1, 
                    'Tyler Allgeier': 2, 
                    'James Conner': 4, 
                    'Zonovan Knight': 3, 
                    'Jonathon Brooks': 2, 
                    'AJ Dillon': 3, 
                    'Trevor Etienne': 4, 
                    'Anthony Tyus III': 5, 
                    'Deshaun Watson': 1, 
                    'Dillon Gabriel': 3, 
                    'Keaton Mitchell': 3, 
                    'Jaret Patterson': 4, 
                    'Terrance Ferguson': 1, 
                    'Max Klare': 4, 
                    'Rashid Shaheed': 2,
                    'Tory Horton': 4, 
                    'Tyjae Spears': 2, 
                    'Nicholas Singleton': 3, 
                    'Michael Carter': 4,
                    'Raheim Sanders': 3,
                    'Dylan Sampson': 2,
                    'Marvin Harrison Jr.': 1,
                    'Michael Wilson': 2
                    }
    df['Depth'] = df['Player'].map(manual_depth).fillna(df['Depth'])
    df['Depth'] = df['Depth'].astype(int)
    df = df.sort_values(['Team', 'Pos.', 'Depth']).reset_index(drop=True)
    return df


def preseasonuseful1(dflist, totalstats, individualtotals):
    if not isinstance(dflist, list):
        raise TypeError("Expected a list of dataframes")
    for file in dflist:
        if not isinstance(file, pd.DataFrame):
            raise TypeError(f"List should contain pandas DataFrames. Got {type(file)}: {file}")
    useful_columns = ['Team', 'Player', 'Pos.', 'Age', 'G', 'PassAtt', 'PassAttStDev', 'PassAtt%', 'PassAtt%StDev', 'Rec', 'RecStDev', 'Rec%', 'Rec%StDev', 'RushAtt', 'RushStDev', 'Rush%', 'Rush%StDev', 'PassYdsperAtt', 'PassYdsperAttStDev', 'PassTDperAtt', 'PassTDperAttStDev', 'IntperAtt', 'IntperAttStDev', 'RecYdsperAtt', 'RecYdsperAttStDev', 'RecTDperAtt', 'RecTDperAttStDev', 'RushYdsperAtt', 'RushYdsperAttStDev', 'RushTDperAtt', 'RushTDperAttStDev']
    existing_columns = [col for col in useful_columns if col in totalstats.columns and col not in ['G', 'PassAttStDev', 'PassAtt%', 'PassAtt%StDev', 'RecStDev', 'Rec%', 'Rec%StDev', 'RushStDev', 'Rush%', 'Rush%StDev', 'PassYdsperAtt', 'PassYdsperAttStDev', 'PassTDperAtt', 'PassTDperAttStDev', 'IntperAtt', 'IntperAttStDev', 'RecYdsperAtt', 'RecYdsperAttStDev', 'RecTDperAtt', 'RecTDperAttStDev', 'RushYdsperAtt', 'RushYdsperAttStDev', 'RushTDperAtt', 'RushTDperAttStDev']]
    Useful = totalstats[existing_columns].copy()

    calculated_columns = ['G', 'PassAttStDev', 'PassAtt%', 'PassAtt%StDev', 'RecStDev', 'Rec%', 'Rec%StDev', 'RushStDev', 'Rush%', 'Rush%StDev', 'PassYdsperAtt', 'PassYdsperAttStDev', 'PassTDperAtt', 'PassTDperAttStDev', 'IntperAtt', 'IntperAttStDev', 'RecYdsperAtt', 'RecYdsperAttStDev', 'RecTDperAtt', 'RecTDperAttStDev', 'RushYdsperAtt', 'RushYdsperAttStDev', 'RushTDperAtt', 'RushTDperAttStDev']
    for col in calculated_columns:
        if col not in Useful.columns:
            Useful[col] = 0.0
    stat_fields = ['PassAtt', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    player_stats = defaultdict(lambda: defaultdict(list))
    player_games_played = defaultdict(int)
    for df in dflist:
        if 'Player' not in df.columns:
            continue
        players_in_game = set()
        for row in df.itertuples(index=False):
            player = getattr(row, 'Player')
            players_in_game.add(player)
            stats = {}
            for stat in stat_fields:
                if hasattr(row, stat):
                    value = getattr(row, stat)
                    stats[stat] = value if pd.notnull(value) else 0
                else:
                    stats[stat] = 0
            for stat in ['PassAtt', 'Rec', 'RushAtt']:
                player_stats[player][stat].append(stats[stat])
            if stats['PassAtt'] != 0:
                player_stats[player]['PassYdsperAtt'].append(stats['PassYds'] / stats['PassAtt'])
                player_stats[player]['PassTDperAtt'].append(stats['PassTD'] / stats['PassAtt'])
                player_stats[player]['IntperAtt'].append(stats['Int'] / stats['PassAtt'])
            else:
                player_stats[player]['PassYdsperAtt'].append(0)
                player_stats[player]['PassTDperAtt'].append(0)
                player_stats[player]['IntperAtt'].append(0)
            if stats['Rec'] != 0:
                player_stats[player]['RecYdsperAtt'].append(stats['RecYds'] / stats['Rec'])
                player_stats[player]['RecTDperAtt'].append(stats['RecTD'] / stats['Rec'])
            else:
                player_stats[player]['RecYdsperAtt'].append(0)
                player_stats[player]['RecTDperAtt'].append(0)
            if stats['RushAtt'] != 0:
                player_stats[player]['RushYdsperAtt'].append(stats['RushYds'] / stats['RushAtt'])
                player_stats[player]['RushTDperAtt'].append(stats['RushTD'] / stats['RushAtt'])
            else:
                player_stats[player]['RushYdsperAtt'].append(0)
                player_stats[player]['RushTDperAtt'].append(0)
        for player in players_in_game:
            player_games_played[player] += 1
    individualtotals = individualtotals.set_index('Player')
    def get_stdev(values):
        if len(values) >= 2:
            return np.std(values, ddof=1)
        return 0
    rate_columns = ['PassYdsperAtt', 'PassTDperAtt', 'IntperAtt', 'RecYdsperAtt', 'RecTDperAtt', 'RushYdsperAtt', 'RushTDperAtt']
    for i, row in Useful.iterrows():
        player = row['Player']
        team = row['Team']
        Useful.at[i, 'G'] = player_games_played.get(player, 0)
        Useful.at[i, 'PassAttStDev'] = get_stdev(player_stats[player]['PassAtt'])
        Useful.at[i, 'RecStDev'] = get_stdev(player_stats[player]['Rec'])
        Useful.at[i, 'RushStDev'] = get_stdev(player_stats[player]['RushAtt'])
        team_pass_att = individualtotals.at[player, 'TeamTotalPassAtt'] if player in individualtotals.index and 'TeamTotalPassAtt' in individualtotals.columns else 0
        team_rec = individualtotals.at[player, 'TeamTotalRec'] if player in individualtotals.index and 'TeamTotalRec' in individualtotals.columns else 0
        team_rush_att = individualtotals.at[player, 'TeamTotalRushAtt'] if player in individualtotals.index and 'TeamTotalRushAtt' in individualtotals.columns else 0
        Useful.at[i, 'PassAtt%'] = row['PassAtt'] / team_pass_att if team_pass_att != 0 else 0
        Useful.at[i, 'Rec%'] = row['Rec'] / team_rec if team_rec != 0 else 0
        Useful.at[i, 'Rush%'] = row['RushAtt'] / team_rush_att if team_rush_att != 0 else 0
        Useful.at[i, 'PassAtt%StDev'] = get_stdev([x / team_pass_att if team_pass_att != 0 else 0 for x in player_stats[player]['PassAtt']])
        Useful.at[i, 'Rec%StDev'] = get_stdev([x / team_rec if team_rec != 0 else 0 for x in player_stats[player]['Rec']])
        Useful.at[i, 'Rush%StDev'] = get_stdev([x / team_rush_att if team_rush_att != 0 else 0 for x in player_stats[player]['RushAtt']])
        for rate in rate_columns:
            values = player_stats[player][rate]
            Useful.at[i, rate] = np.mean(values) if len(values) > 0 else 0
            Useful.at[i, f'{rate}StDev'] = get_stdev(values)
    Useful = Useful[useful_columns]
    return Useful


def preseasonuseful(dflist, totalstats, individualtotals):
    if not isinstance(dflist, list):
        raise TypeError("Expected a list of dataframes")
    for file in dflist:
        if not isinstance(file, pd.DataFrame):
            raise TypeError(f"List should contain pandas DataFrames. Got {type(file)}: {file}")
    useful_columns = ['Team', 'Player', 'Pos.', 'Age', 'G', 'PassAtt', 'PassAttStDev', 'PassAttperGame', 'PassAtt%', 'PassAtt%StDev', 'Rec', 'RecStDev', 'RecperGame', 'Rec%', 'Rec%StDev', 'RushAtt', 'RushStDev', 'RushAttperGame', 'Rush%', 'Rush%StDev', 'PassYdsperAtt', 'PassYdsperAttStDev', 'PassTDperAtt', 'PassTDperAttStDev', 'IntperAtt', 'IntperAttStDev', 'RecYdsperAtt', 'RecYdsperAttStDev', 'RecTDperAtt', 'RecTDperAttStDev', 'RushYdsperAtt', 'RushYdsperAttStDev', 'RushTDperAtt', 'RushTDperAttStDev']
    calculated_columns = ['G', 'PassAttStDev', 'PassAttperGame', 'PassAtt%', 'PassAtt%StDev', 'RecStDev', 'RecperGame', 'Rec%', 'Rec%StDev', 'RushStDev', 'RushAttperGame', 'Rush%', 'Rush%StDev', 'PassYdsperAtt', 'PassYdsperAttStDev', 'PassTDperAtt', 'PassTDperAttStDev', 'IntperAtt', 'IntperAttStDev', 'RecYdsperAtt', 'RecYdsperAttStDev', 'RecTDperAtt', 'RecTDperAttStDev', 'RushYdsperAtt', 'RushYdsperAttStDev', 'RushTDperAtt', 'RushTDperAttStDev']
    existing_columns = [col for col in useful_columns if col in totalstats.columns and col not in calculated_columns]
    Useful = totalstats[existing_columns].copy()
    for col in calculated_columns:
        if col not in Useful.columns:
            Useful[col] = 0.0
    stat_fields = ['PassAtt', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    player_stats = defaultdict(lambda: defaultdict(list))
    player_games_played = defaultdict(int)
    for df in dflist:
        if 'Player' not in df.columns:
            continue
        players_in_game = set()
        for row in df.itertuples(index=False):
            player = getattr(row, 'Player')
            players_in_game.add(player)
            stats = {}
            for stat in stat_fields:
                if hasattr(row, stat):
                    value = getattr(row, stat)
                    stats[stat] = value if pd.notnull(value) else 0
                else:
                    stats[stat] = 0
            for stat in ['PassAtt', 'Rec', 'RushAtt']:
                player_stats[player][stat].append(stats[stat])
            if stats['PassAtt'] != 0:
                player_stats[player]['PassYdsperAtt'].append(stats['PassYds'] / stats['PassAtt'])
                player_stats[player]['PassTDperAtt'].append(stats['PassTD'] / stats['PassAtt'])
                player_stats[player]['IntperAtt'].append(stats['Int'] / stats['PassAtt'])
            else:
                player_stats[player]['PassYdsperAtt'].append(0)
                player_stats[player]['PassTDperAtt'].append(0)
                player_stats[player]['IntperAtt'].append(0)
            if stats['Rec'] != 0:
                player_stats[player]['RecYdsperAtt'].append(stats['RecYds'] / stats['Rec'])
                player_stats[player]['RecTDperAtt'].append(stats['RecTD'] / stats['Rec'])
            else:
                player_stats[player]['RecYdsperAtt'].append(0)
                player_stats[player]['RecTDperAtt'].append(0)
            if stats['RushAtt'] != 0:
                player_stats[player]['RushYdsperAtt'].append(stats['RushYds'] / stats['RushAtt'])
                player_stats[player]['RushTDperAtt'].append(stats['RushTD'] / stats['RushAtt'])
            else:
                player_stats[player]['RushYdsperAtt'].append(0)
                player_stats[player]['RushTDperAtt'].append(0)
        for player in players_in_game:
            player_games_played[player] += 1
    individualtotals = individualtotals.set_index('Player')
    def get_stdev(values):
        if len(values) >= 2:
            return np.std(values, ddof=1)
        return 0
    rate_columns = ['PassYdsperAtt', 'PassTDperAtt', 'IntperAtt', 'RecYdsperAtt', 'RecTDperAtt', 'RushYdsperAtt', 'RushTDperAtt']
    for i, row in Useful.iterrows():
        player = row['Player']
        team = row['Team']
        games = player_games_played.get(player, 0)
        Useful.at[i, 'G'] = games
        Useful.at[i, 'PassAttperGame'] = row['PassAtt'] / games if games != 0 else 0
        Useful.at[i, 'RecperGame'] = row['Rec'] / games if games != 0 else 0
        Useful.at[i, 'RushAttperGame'] = row['RushAtt'] / games if games != 0 else 0
        Useful.at[i, 'PassAttStDev'] = get_stdev(player_stats[player]['PassAtt'])
        Useful.at[i, 'RecStDev'] = get_stdev(player_stats[player]['Rec'])
        Useful.at[i, 'RushStDev'] = get_stdev(player_stats[player]['RushAtt'])
        team_pass_att = individualtotals.at[player, 'TeamTotalPassAtt'] if player in individualtotals.index and 'TeamTotalPassAtt' in individualtotals.columns else 0
        team_rec = individualtotals.at[player, 'TeamTotalRec'] if player in individualtotals.index and 'TeamTotalRec' in individualtotals.columns else 0
        team_rush_att = individualtotals.at[player, 'TeamTotalRushAtt'] if player in individualtotals.index and 'TeamTotalRushAtt' in individualtotals.columns else 0
        Useful.at[i, 'PassAtt%'] = row['PassAtt'] / team_pass_att if team_pass_att != 0 else 0
        Useful.at[i, 'Rec%'] = row['Rec'] / team_rec if team_rec != 0 else 0
        Useful.at[i, 'Rush%'] = row['RushAtt'] / team_rush_att if team_rush_att != 0 else 0
        Useful.at[i, 'PassAtt%StDev'] = get_stdev([x / team_pass_att if team_pass_att != 0 else 0 for x in player_stats[player]['PassAtt']])
        Useful.at[i, 'Rec%StDev'] = get_stdev([x / team_rec if team_rec != 0 else 0 for x in player_stats[player]['Rec']])
        Useful.at[i, 'Rush%StDev'] = get_stdev([x / team_rush_att if team_rush_att != 0 else 0 for x in player_stats[player]['RushAtt']])
        #for rate in rate_columns:
        #    values = player_stats[player][rate]
        #    Useful.at[i, rate] = np.mean(values) if len(values) > 0 else 0
        #    Useful.at[i, f'{rate}StDev'] = get_stdev(values)
        for rate in rate_columns:
            values = player_stats[player][rate]
            Useful.at[i, f'{rate}StDev'] = get_stdev(values)
            if rate == 'PassYdsperAtt':
                Useful.at[i, rate] = totalstats.loc[totalstats['Player'] == player, 'PassYds'].iloc[0] / totalstats.loc[totalstats['Player'] == player, 'PassAtt'].iloc[0] if totalstats.loc[totalstats['Player'] == player, 'PassAtt'].iloc[0] != 0 else 0
            elif rate == 'PassTDperAtt':
                Useful.at[i, rate] = totalstats.loc[totalstats['Player'] == player, 'PassTD'].iloc[0] / totalstats.loc[totalstats['Player'] == player, 'PassAtt'].iloc[0] if totalstats.loc[totalstats['Player'] == player, 'PassAtt'].iloc[0] != 0 else 0
            elif rate == 'IntperAtt':
                Useful.at[i, rate] = totalstats.loc[totalstats['Player'] == player, 'Int'].iloc[0] / totalstats.loc[totalstats['Player'] == player, 'PassAtt'].iloc[0] if totalstats.loc[totalstats['Player'] == player, 'PassAtt'].iloc[0] != 0 else 0
            elif rate == 'RecYdsperAtt':
                Useful.at[i, rate] = totalstats.loc[totalstats['Player'] == player, 'RecYds'].iloc[0] / totalstats.loc[totalstats['Player'] == player, 'Rec'].iloc[0] if totalstats.loc[totalstats['Player'] == player, 'Rec'].iloc[0] != 0 else 0
            elif rate == 'RecTDperAtt':
                Useful.at[i, rate] = totalstats.loc[totalstats['Player'] == player, 'RecTD'].iloc[0] / totalstats.loc[totalstats['Player'] == player, 'Rec'].iloc[0] if totalstats.loc[totalstats['Player'] == player, 'Rec'].iloc[0] != 0 else 0
            elif rate == 'RushYdsperAtt':
                Useful.at[i, rate] = totalstats.loc[totalstats['Player'] == player, 'RushYds'].iloc[0] / totalstats.loc[totalstats['Player'] == player, 'RushAtt'].iloc[0] if totalstats.loc[totalstats['Player'] == player, 'RushAtt'].iloc[0] != 0 else 0
            elif rate == 'RushTDperAtt':
                Useful.at[i, rate] = totalstats.loc[totalstats['Player'] == player, 'RushTD'].iloc[0] / totalstats.loc[totalstats['Player'] == player, 'RushAtt'].iloc[0] if totalstats.loc[totalstats['Player'] == player, 'RushAtt'].iloc[0] != 0 else 0

    Useful = Useful[useful_columns]
    return Useful


def apply_depth_limits(useful):
    depth_limits = {'QB': 2, 'RB': 3, 'TE': 3, 'WR': 5}
    useful = useful.copy()
    useful['DepthNumeric'] = pd.to_numeric(useful['Depth'], errors='coerce')
    keep = ~useful['Pos.'].isin(depth_limits) | (useful['DepthNumeric'] <= useful['Pos.'].map(depth_limits))
    useful = useful.loc[keep].drop(columns='DepthNumeric').reset_index(drop=True)
    return useful


def designate_rookies(useful):
    useful = useful.copy()
    stat_columns = ['G', 'PassAtt', 'PassAttStDev', 'PassAttperGame', 'PassAtt%', 'PassAtt%StDev', 'Rec', 'RecStDev', 'RecperGame', 'Rec%', 'Rec%StDev', 'RushAtt', 'RushStDev', 'RushAttperGame', 'Rush%', 'Rush%StDev', 'PassYdsperAtt', 'PassYdsperAttStDev', 'PassTDperAtt', 'PassTDperAttStDev', 'IntperAtt', 'IntperAttStDev', 'RecYdsperAtt', 'RecYdsperAttStDev', 'RecTDperAtt', 'RecTDperAttStDev', 'RushYdsperAtt', 'RushYdsperAttStDev', 'RushTDperAtt', 'RushTDperAttStDev']
    manual_rookies = ['Deshaun Watson']
    useful['Rookie'] = ((useful['Age'] < 25) & (useful[stat_columns].fillna(0) == 0).all(axis=1)).astype(int)
    useful.loc[useful['Player'].isin(manual_rookies), 'Rookie'] = 1
    return useful


def assign_rookie_rates(Useful):
    Useful = Useful.copy()
    rate_columns = ['PassAttperGame', 'RecperGame', 'RushAttperGame', 'PassYdsperAtt', 'PassTDperAtt', 'IntperAtt', 'RecYdsperAtt', 'RecTDperAtt', 'RushYdsperAtt', 'RushTDperAtt']
    stdev_columns = ['PassAttStDev', 'RecStDev', 'RushStDev', 'PassYdsperAttStDev', 'PassTDperAttStDev', 'IntperAttStDev', 'RecYdsperAttStDev', 'RecTDperAttStDev', 'RushYdsperAttStDev', 'RushTDperAttStDev']
    for pos in Useful['Pos.'].unique():
        historical = Useful[(Useful['Pos.'] == pos) & (Useful['Rookie'] == 0)]
        rookies = Useful[(Useful['Pos.'] == pos) & (Useful['Rookie'] == 1)]
        if len(rookies) == 0 or len(historical) == 0:
            continue
        for rate in rate_columns:
            average_rate = pd.to_numeric(historical[rate], errors='coerce').replace([np.inf, -np.inf], np.nan).dropna().mean()
            if pd.isna(average_rate):
                average_rate = 0.0
            Useful.loc[rookies.index, rate] = average_rate
        for stdev in stdev_columns:
            average_stdev = pd.to_numeric(historical[stdev], errors='coerce').replace([np.inf, -np.inf], np.nan).dropna().mean()
            if pd.isna(average_stdev):
                average_stdev = 0.0
            Useful.loc[rookies.index, stdev] = average_stdev
    return Useful


def adjust_qb_role_changes(Useful):
    Useful = Useful.copy()
    for team, team_df in Useful.groupby('Team'):
        qbs = team_df[team_df['Pos.'] == 'QB'].copy()
        if len(qbs) == 0:
            continue
        qbs['DepthNumeric'] = pd.to_numeric(qbs['Depth'], errors='coerce')
        qb1 = qbs[qbs['DepthNumeric'] == 1]
        if len(qb1) == 0:
            continue
        qb1_idx = qb1.index[0]
        qb1_games = pd.to_numeric(Useful.at[qb1_idx, 'G'], errors='coerce')
        qb1_games = 0 if pd.isna(qb1_games) else qb1_games
        backup_games = min(3, max(0, 17 - qb1_games))
        for idx in qbs.index:
            depth = pd.to_numeric(Useful.at[idx, 'Depth'], errors='coerce')
            if pd.isna(depth) or depth <= 1:
                continue
            Useful.at[idx, 'PassAttperGame'] = pd.to_numeric(Useful.at[idx, 'PassAttperGame'], errors='coerce')
            if pd.isna(Useful.at[idx, 'PassAttperGame']):
                Useful.at[idx, 'PassAttperGame'] = 0.0
            Useful.at[idx, 'PassAttperGame'] *= backup_games / 17
    return Useful


def adjust_rookie_percentages(Useful):
    Useful = Useful.copy()
    percentage_columns = ['PassAtt%', 'Rec%', 'Rush%']
    for team, team_df in Useful.groupby('Team'):
        for percentage_column in percentage_columns:
            team_df[percentage_column] = pd.to_numeric(team_df[percentage_column], errors='coerce').fillna(0)
            rookies = team_df[team_df['Rookie'] == 1].copy()
            historical = team_df[team_df['Rookie'] == 0].copy()
            if len(rookies) == 0 or len(historical) == 0:
                continue
            historical = historical.sort_values(percentage_column, ascending=False)
            percentages = historical[percentage_column].tolist()
            rookies = rookies.sort_values('Depth')
            for rookie_idx in rookies.index:
                rookie_depth = pd.to_numeric(team_df.loc[rookie_idx, 'Depth'], errors='coerce')
                if pd.isna(rookie_depth):
                    continue
                rookie_depth = int(rookie_depth)
                if rookie_depth < 1:
                    continue
                insert_position = rookie_depth - 1
                if insert_position < len(percentages):
                    rookie_percentage = percentages[insert_position]
                else:
                    rookie_percentage = 0
                percentages.insert(insert_position, rookie_percentage)
            percentages = np.array(percentages[:len(team_df)], dtype=float)
            if percentages.sum() > 0:
                percentages = percentages / percentages.sum()
            ranked_players = team_df.sort_values(percentage_column, ascending=False).copy()
            for i, idx in enumerate(ranked_players.index):
                if i < len(percentages):
                    Useful.loc[idx, percentage_column] = percentages[i]
    return Useful


def limit_preseason_tds(df, depth_col='Depth', pos_col='Pos.'):
    result = df.copy()
    receiving_td_limits = {'Los Angeles Rams': 46, 'Cincinnati Bengals': 36, 'Detroit Lions': 35, 'San Francisco 49ers': 33, 'Dallas Cowboys': 31, 'New England Patriots': 31, 'Arizona Cardinals': 29, 'Buffalo Bills': 29, 'Jacksonville Jaguars': 29, 'Chicago Bears': 28, 'Green Bay Packers': 26, 'Los Angeles Chargers': 26, 'Philadelphia Eagles': 26, 'Pittsburgh Steelers': 26, 'Tampa Bay Buccaneers': 26, 'Denver Broncos': 25, 'Indianapolis Colts': 25, 'Seattle Seahawks': 25, 'Carolina Panthers': 24, 'Houston Texans': 24, 'Baltimore Ravens': 23, 'Kansas City Chiefs': 23, 'Miami Dolphins': 23, 'New York Giants': 21, 'Las Vegas Raiders': 20, 'Atlanta Falcons': 19, 'New Orleans Saints': 19, 'Washington Commanders': 18, 'Minnesota Vikings': 16, 'Cleveland Browns': 15, 'New York Jets': 15, 'Tennessee Titans': 15}
    rushing_td_limits = {'Buffalo Bills': 30, 'Indianapolis Colts': 27, 'Baltimore Ravens': 23, 'Jacksonville Jaguars': 22, 'New England Patriots': 22, 'New York Giants': 22, 'Detroit Lions': 21, 'Washington Commanders': 20, 'Chicago Bears': 19, 'Seattle Seahawks': 19, 'Dallas Cowboys': 18, 'Denver Broncos': 18, 'Green Bay Packers': 18, 'Atlanta Falcons': 17, 'Los Angeles Rams': 17, 'Philadelphia Eagles': 17, 'Pittsburgh Steelers': 17, 'Kansas City Chiefs': 16, 'Minnesota Vikings': 15, 'San Francisco 49ers': 15, 'Miami Dolphins': 15, 'Tampa Bay Buccaneers': 14, 'Cincinnati Bengals': 13, 'New York Jets': 11, 'Cleveland Browns': 11, 'Los Angeles Chargers': 10, 'Arizona Cardinals': 10, 'Carolina Panthers': 9, 'Houston Texans': 9, 'New Orleans Saints': 9, 'Tennessee Titans': 9, 'Las Vegas Raiders': 5}
    receiving_order = [('TE', 3), ('WR', 5), ('WR', 4), ('RB', 3), ('TE', 2), ('WR', 3), ('RB', 2), ('WR', 2), ('RB', 1), ('TE', 1), ('WR', 1)]
    rushing_order = [('TE', 3), ('TE', 2), ('TE', 1), ('WR', 5), ('WR', 4), ('WR', 3), ('WR', 2), ('RB', 3), ('WR', 1), ('RB', 2), ('RB', 1)]
    for team in result['Team'].dropna().unique():
        team_mask = result['Team'].eq(team)
        if team in receiving_td_limits:
            maximum = receiving_td_limits[team]
            projected_rec = result.loc[team_mask, 'RecperGame'] * 17 * result.loc[team_mask, 'RecTDperAtt']
            current_total = projected_rec.sum()
            amount_to_remove = current_total - maximum
            if amount_to_remove > 0:
                for position, depth in receiving_order:
                    if amount_to_remove <= 0:
                        break
                    player_mask = team_mask & result[pos_col].eq(position) & result[depth_col].eq(depth)
                    for idx in result.index[player_mask]:
                        if amount_to_remove <= 0:
                            break
                        rec_per_game = result.at[idx, 'RecperGame']
                        rate = result.at[idx, 'RecTDperAtt']
                        if pd.isna(rec_per_game) or pd.isna(rate) or rec_per_game <= 0 or rate <= 0:
                            continue
                        projected_receptions = rec_per_game * 17
                        player_tds = projected_receptions * rate
                        removal = min(player_tds, amount_to_remove)
                        new_tds = player_tds - removal
                        result.at[idx, 'RecTDperAtt'] = new_tds / projected_receptions
                        amount_to_remove -= removal
        if team in rushing_td_limits:
            maximum = rushing_td_limits[team]
            projected_rush = result.loc[team_mask, 'RushAttperGame'] * 17 * result.loc[team_mask, 'RushTDperAtt']
            current_total = projected_rush.sum()
            amount_to_remove = current_total - maximum
            if amount_to_remove > 0:
                for position, depth in rushing_order:
                    if amount_to_remove <= 0:
                        break
                    player_mask = team_mask & result[pos_col].eq(position) & result[depth_col].eq(depth)
                    for idx in result.index[player_mask]:
                        if amount_to_remove <= 0:
                            break
                        rush_per_game = result.at[idx, 'RushAttperGame']
                        rate = result.at[idx, 'RushTDperAtt']
                        if pd.isna(rush_per_game) or pd.isna(rate) or rush_per_game <= 0 or rate <= 0:
                            continue
                        projected_attempts = rush_per_game * 17
                        player_tds = projected_attempts * rate
                        removal = min(player_tds, amount_to_remove)
                        new_tds = player_tds - removal
                        result.at[idx, 'RushTDperAtt'] = new_tds / projected_attempts
                        amount_to_remove -= removal
    return result






def preseason_adjustments(Useful):
    qb_role_changes = ['Shedeur Sanders', 'Kirk Cousins']
    depth_limits = {'QB': 2, 'RB': 3, 'TE': 3, 'WR': 5}
    rate_columns = ['PassYdsperAtt', 'PassTDperAtt', 'IntperAtt', 'RecYdsperAtt', 'RecTDperAtt', 'RushYdsperAtt', 'RushTDperAtt']
    stdev_map = {'PassYdsperAtt': 'PassYdsperAttStDev', 'PassTDperAtt': 'PassTDperAttStDev', 'IntperAtt': 'IntperAttStDev', 'RecYdsperAtt': 'RecYdsperAttStDev', 'RecTDperAtt': 'RecTDperAttStDev', 'RushYdsperAtt': 'RushYdsperAttStDev', 'RushTDperAtt': 'RushTDperAttStDev'}
    opportunity_map = {'QB': ['PassAtt/G'], 'RB': ['RushAtt/G', 'Rec/G'], 'WR': ['Rec/G', 'RushAtt/G'], 'TE': ['Rec/G', 'RushAtt/G']}
    position_targets = {'QB': {'PassAtt/G': 550 / 17}, 'RB': {'RushAtt/G': 455 / 17, 'Rec/G': 73 / 17}, 'WR': {'Rec/G': 188 / 17}, 'TE': {'Rec/G': 90 / 17}}
    Useful = Useful.copy().fillna(0)
    Useful['G'] = pd.to_numeric(Useful['G'], errors='coerce').fillna(0)
    Useful['PassAtt'] = pd.to_numeric(Useful['PassAtt'], errors='coerce').fillna(0).astype(float)
    Useful['RushAtt'] = pd.to_numeric(Useful['RushAtt'], errors='coerce').fillna(0).astype(float)
    Useful['Rec'] = pd.to_numeric(Useful['Rec'], errors='coerce').fillna(0).astype(float)
    Useful['PassAtt/G'] = np.where(Useful['G'] > 0, Useful['PassAtt'] / Useful['G'], 0.0)
    Useful['RushAtt/G'] = np.where(Useful['G'] > 0, Useful['RushAtt'] / Useful['G'], 0.0)
    Useful['Rec/G'] = np.where(Useful['G'] > 0, Useful['Rec'] / Useful['G'], 0.0)
    for col in rate_columns:
        if col not in Useful.columns:
            Useful[col] = 0.0
        Useful[col] = pd.to_numeric(Useful[col], errors='coerce').fillna(0).astype(float)
        if stdev_map[col] not in Useful.columns:
            Useful[stdev_map[col]] = 0.0
        Useful[stdev_map[col]] = pd.to_numeric(Useful[stdev_map[col]], errors='coerce').fillna(0).astype(float)
    for team, team_df in Useful.groupby('Team'):
        for pos, max_depth in depth_limits.items():
            pos_df = team_df[team_df['Pos.'] == pos].copy()
            if len(pos_df) == 0:
                continue
            depth_numeric = pd.to_numeric(pos_df['Depth'], errors='coerce')
            eligible = pos_df[depth_numeric <= max_depth].copy()
            removed = pos_df[depth_numeric > max_depth].copy()
            if len(eligible) == 0:
                continue
            historical = eligible[eligible['G'] > 0].copy()
            rookies = eligible[eligible['G'] == 0].copy()
            for rate in rate_columns:
                if len(rookies) == 0:
                    continue
                if rate.startswith('Pass'):
                    weight_col = 'PassAtt'
                elif rate.startswith('Rec'):
                    weight_col = 'Rec'
                else:
                    weight_col = 'RushAtt'
                valid = historical[pd.to_numeric(historical[weight_col], errors='coerce').fillna(0) > 0]
                if len(valid) > 0:
                    values = pd.to_numeric(valid[rate], errors='coerce').fillna(0).to_numpy()
                    weights = pd.to_numeric(valid[weight_col], errors='coerce').fillna(0).to_numpy()
                    weighted_rate = np.average(values, weights=weights)
                    weighted_variance = np.average((values - weighted_rate) ** 2, weights=weights)
                    weighted_stdev = np.sqrt(weighted_variance)
                else:
                    weighted_rate = 0.0
                    weighted_stdev = 0.0
                Useful.loc[rookies.index, rate] = weighted_rate
                Useful.loc[rookies.index, stdev_map[rate]] = weighted_stdev
            for opportunity in opportunity_map[pos]:
                if len(removed) > 0:
                    for idx in removed.index:
                        removed_value = pd.to_numeric(Useful.at[idx, opportunity], errors='coerce')
                        if pd.isna(removed_value):
                            removed_value = 0.0
                        redistribute = True
                        if pos == 'QB' and opportunity == 'PassAtt/G' and removed_value > 5:
                            redistribute = False
                        if redistribute and removed_value > 0:
                            share = removed_value / len(eligible)
                            Useful.loc[eligible.index, opportunity] = pd.to_numeric(Useful.loc[eligible.index, opportunity], errors='coerce').fillna(0) + share
                        Useful.at[idx, opportunity] = 0.0
            if pos == 'QB':
                qb1_candidates = eligible[pd.to_numeric(eligible['Depth'], errors='coerce') == 1]
                if len(qb1_candidates) > 0:
                    qb1_idx = qb1_candidates.index[0]
                    qb1_pass_att_g = pd.to_numeric(Useful.at[qb1_idx, 'PassAtt/G'], errors='coerce')
                    if pd.isna(qb1_pass_att_g):
                        qb1_pass_att_g = 0.0
                    if qb1_pass_att_g < 15:
                        qb_target = position_targets['QB']['PassAtt/G']
                        qb1_adjustment = 0.80 * max(qb_target - qb1_pass_att_g, 0)
                        Useful.at[qb1_idx, 'PassAtt/G'] = qb1_pass_att_g + qb1_adjustment
            if len(rookies) > 0:
                for opportunity, target in position_targets[pos].items():
                    if pos == 'QB' and opportunity == 'PassAtt/G':
                        qb_pool = team_df[team_df['Pos.'] == 'QB'].copy()
                        qb_pool['DepthNumeric'] = pd.to_numeric(qb_pool['Depth'], errors='coerce')
                        qb_pool['PassAtt/G'] = pd.to_numeric(qb_pool['PassAtt/G'], errors='coerce').fillna(0)
                        historical_opportunity_total = 0.0
                        for idx in qb_pool.index:
                            depth = qb_pool.at[idx, 'DepthNumeric']
                            attempts_per_game = qb_pool.at[idx, 'PassAtt/G']
                            games = pd.to_numeric(qb_pool.at[idx, 'G'], errors='coerce')
                            if pd.isna(games):
                                games = 0
                            if games <= 0:
                                continue
                            if depth > 2 and attempts_per_game > 5:
                                continue
                            contribution = attempts_per_game
                            player_name = qb_pool.at[idx, 'Player']
                            if player_name in qb_role_changes:
                                contribution *= 3 / 17
                            historical_opportunity_total += contribution
                    else:
                        historical_opportunity_total = pd.to_numeric(historical[opportunity], errors='coerce').fillna(0).sum()
                    rookie_remainder = max(target - historical_opportunity_total, 0)
                    if len(rookies) == 1:
                        Useful.loc[rookies.index, opportunity] = rookie_remainder
                    else:
                        rookie_depths = pd.to_numeric(rookies['Depth'], errors='coerce').fillna(max_depth).clip(lower=1)
                        weights = 1 / rookie_depths
                        weights = weights / weights.sum()
                        Useful.loc[rookies.index, opportunity] = rookie_remainder * weights
            statistical_columns = [col for col in Useful.columns if col not in ['Team', 'Player', 'Pos.', 'Age', 'Depth']]
            if len(removed) > 0:
                Useful.loc[removed.index, statistical_columns] = 0.0
    Useful['PassYds'] = pd.to_numeric(Useful['PassAtt/G'], errors='coerce').fillna(0) * pd.to_numeric(Useful['PassYdsperAtt'], errors='coerce').fillna(0)
    Useful['PassTD'] = pd.to_numeric(Useful['PassAtt/G'], errors='coerce').fillna(0) * pd.to_numeric(Useful['PassTDperAtt'], errors='coerce').fillna(0)
    Useful['Int'] = pd.to_numeric(Useful['PassAtt/G'], errors='coerce').fillna(0) * pd.to_numeric(Useful['IntperAtt'], errors='coerce').fillna(0)
    Useful['RecYds'] = pd.to_numeric(Useful['Rec/G'], errors='coerce').fillna(0) * pd.to_numeric(Useful['RecYdsperAtt'], errors='coerce').fillna(0)
    Useful['RecTD'] = pd.to_numeric(Useful['Rec/G'], errors='coerce').fillna(0) * pd.to_numeric(Useful['RecTDperAtt'], errors='coerce').fillna(0)
    Useful['RushYds'] = pd.to_numeric(Useful['RushAtt/G'], errors='coerce').fillna(0) * pd.to_numeric(Useful['RushYdsperAtt'], errors='coerce').fillna(0)
    Useful['RushTD'] = pd.to_numeric(Useful['RushAtt/G'], errors='coerce').fillna(0) * pd.to_numeric(Useful['RushTDperAtt'], errors='coerce').fillna(0)
    Useful = Useful.fillna(0)
    return Useful


def balance_passing_receiving(PreS):
    PreS = PreS.copy()
    numeric_columns = ['PassAtt', 'PassYds', 'PassTD', 'Rec', 'RecYds', 'RecTD']
    for col in numeric_columns:
        PreS[col] = pd.to_numeric(PreS[col], errors='coerce').fillna(0.0)
    for team, team_df in PreS.groupby('Team'):
        pass_yards_total = team_df['PassYds'].sum()
        rec_yards_total = team_df['RecYds'].sum()
        average_yards = (pass_yards_total + rec_yards_total) / 2
        if pass_yards_total > 0:
            pass_yards_ratio = average_yards / pass_yards_total
            pass_att_ratio = 1 + ((pass_yards_ratio - 1) * 0.5)
            PreS.loc[team_df.index, 'PassYds'] = team_df['PassYds'] * pass_yards_ratio
            PreS.loc[team_df.index, 'PassAtt'] = team_df['PassAtt'] * pass_att_ratio
        if rec_yards_total > 0:
            rec_yards_ratio = average_yards / rec_yards_total
            PreS.loc[team_df.index, 'RecYds'] = team_df['RecYds'] * rec_yards_ratio
            PreS.loc[team_df.index, 'Rec'] = team_df['Rec'] * rec_yards_ratio
        pass_td_total = team_df['PassTD'].sum()
        rec_td_total = team_df['RecTD'].sum()
        average_tds = (pass_td_total + rec_td_total) / 2
        if pass_td_total > 0:
            pass_td_ratio = average_tds / pass_td_total
            PreS.loc[team_df.index, 'PassTD'] = team_df['PassTD'] * pass_td_ratio
        if rec_td_total > 0:
            rec_td_ratio = average_tds / rec_td_total
            PreS.loc[team_df.index, 'RecTD'] = team_df['RecTD'] * rec_td_ratio
    PreS = PreS.round(1)
    return PreS


def PreSdataframe1(useful, teamtotals, week, schedule):
    statcolumns = ['Player', 'Team', 'Pos.', 'Age', 'PPR', 'STD', 'PassAtt', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    PreS = pd.DataFrame()
    PreS['Player'] = useful['Player']
    PreS['Team'] = useful['Team']
    PreS['Pos.'] = useful['Pos.']
    PreS['Age'] = useful['Age']
    for stat in statcolumns[4:]:
        PreS[stat] = 0.0
    n_simulations = 10000
    team_stats = teamtotals.set_index('Team').to_dict('index')
    for current_week in range(week, 18):
        predictedrushes = []
        predictedrushyards = []
        predictedrushtds = []
        predictedreceptions = []
        predictedreceivingyards = []
        predictedreceivingtds = []
        predictedpassingattempts = []
        predictedpassingyards = []
        predictedpassingtds = []
        predictedints = []
        pprs = []
        stds = []
        schedule_map = {row[0]: row[current_week] for row in schedule.itertuples(index=False)}
        for i, row in useful.iterrows():
            player_team = row['Team']
            opp = schedule_map.get(player_team, 'BYE')
            randoms = np.random.uniform(-2, 2, (18, n_simulations))
            if opp == 'BYE':
                rushes = np.zeros(n_simulations)
                rushyards = np.zeros(n_simulations)
                rushtds = np.zeros(n_simulations)
                receptions = np.zeros(n_simulations)
                receivingyards = np.zeros(n_simulations)
                receivingtds = np.zeros(n_simulations)
                passingattempts = np.zeros(n_simulations)
                passingyards = np.zeros(n_simulations)
                passingtds = np.zeros(n_simulations)
                ints = np.zeros(n_simulations)
            else:
                opponent = team_stats.get(opp, {})
                rush_attempt_adjustment = opponent.get('RushAttAAV', 0) * row['Rush%']
                rushes = row['RushAtt/G'] + row['RushStDev'] * randoms[0] * (1 + rush_attempt_adjustment * opponent.get('RushAttAAVStDev', 0) * randoms[1])
                rushes = np.clip(rushes, 0, None)
                rush_yards_per_att = row['RushYdsperAtt'] + row['RushYdsperAttStDev'] * randoms[2]
                rushyards = rushes * np.clip(rush_yards_per_att, 0, None)
                rush_td_per_att = row['RushTDperAtt'] + row['RushTDperAttStDev'] * randoms[3]
                rushtds = rushes * np.clip(rush_td_per_att, 0, None)
                rec_adjustment = opponent.get('RecAAV', 0) * row['Rec%']
                receptions = row['Rec/G'] + row['RecStDev'] * randoms[4] * (1 + rec_adjustment * opponent.get('RecAAVStDev', 0) * randoms[5])
                receptions = np.clip(receptions, 0, None)
                rec_yards_per_att = row['RecYdsperAtt'] + row['RecYdsperAttStDev'] * randoms[6]
                receivingyards = receptions * np.clip(rec_yards_per_att, 0, None)
                rec_td_per_att = row['RecTDperAtt'] + row['RecTDperAttStDev'] * randoms[7]
                receivingtds = receptions * np.clip(rec_td_per_att, 0, None)
                pass_attempt_adjustment = opponent.get('PassAttAAV', 0)
                passingattempts = row['PassAtt/G'] + row['PassAttStDev'] * randoms[8] * (1 + pass_attempt_adjustment * opponent.get('PassAttAAVStDev', 0) * randoms[9])
                passingattempts = np.clip(passingattempts, 0, None)
                pass_yards_per_att = row['PassYdsperAtt'] + row['PassYdsperAttStDev'] * randoms[10]
                passingyards = passingattempts * np.clip(pass_yards_per_att, 0, None)
                pass_td_per_att = row['PassTDperAtt'] + row['PassTDperAttStDev'] * randoms[11]
                passingtds = passingattempts * np.clip(pass_td_per_att, 0, None)
                int_per_att = row['IntperAtt'] + row['IntperAttStDev'] * randoms[12]
                ints = passingattempts * np.clip(int_per_att, 0, None)
            rushes_mean = int(np.round(np.nanmean(np.nan_to_num(rushes, nan=0))))
            rushyards_mean = int(np.round(np.nanmean(np.nan_to_num(rushyards, nan=0))))
            rushtds_mean = np.round(np.nanmean(np.nan_to_num(rushtds, nan=0)), 1)
            receptions_mean = int(np.round(np.nanmean(np.nan_to_num(receptions, nan=0))))
            receivingyards_mean = int(np.round(np.nanmean(np.nan_to_num(receivingyards, nan=0))))
            receivingtds_mean = np.round(np.nanmean(np.nan_to_num(receivingtds, nan=0)), 1)
            passingattempts_mean = int(np.round(np.nanmean(np.nan_to_num(passingattempts, nan=0))))
            passingyards_mean = int(np.round(np.nanmean(np.nan_to_num(passingyards, nan=0))))
            passingtds_mean = np.round(np.nanmean(np.nan_to_num(passingtds, nan=0)), 1)
            ints_mean = np.round(np.nanmean(np.nan_to_num(ints, nan=0)), 1)
            predictedrushes.append(rushes_mean)
            predictedrushyards.append(rushyards_mean)
            predictedrushtds.append(rushtds_mean)
            predictedreceptions.append(receptions_mean)
            predictedreceivingyards.append(receivingyards_mean)
            predictedreceivingtds.append(receivingtds_mean)
            predictedpassingattempts.append(passingattempts_mean)
            predictedpassingyards.append(passingyards_mean)
            predictedpassingtds.append(passingtds_mean)
            predictedints.append(ints_mean)
            ppr = rushyards_mean / 10 + receivingyards_mean / 10 + passingyards_mean / 25 + receptions_mean + (rushtds_mean + receivingtds_mean) * 6 + passingtds_mean * 4
            std = rushyards_mean / 10 + receivingyards_mean / 10 + passingyards_mean / 25 + (rushtds_mean + receivingtds_mean) * 6 + passingtds_mean * 4
            pprs.append(ppr)
            stds.append(std)
        PreS['RushAtt'] += predictedrushes
        PreS['RushYds'] += predictedrushyards
        PreS['RushTD'] += predictedrushtds
        PreS['Rec'] += predictedreceptions
        PreS['RecYds'] += predictedreceivingyards
        PreS['RecTD'] += predictedreceivingtds
        PreS['PassAtt'] += predictedpassingattempts
        PreS['PassYds'] += predictedpassingyards
        PreS['PassTD'] += predictedpassingtds
        PreS['Int'] += predictedints
        PreS['PPR'] += pprs
        PreS['STD'] += stds

    for team, team_df in useful.groupby('Team'):
        qbs = team_df[team_df['Pos.'] == 'QB'].copy()
        qbs['DepthNumeric'] = pd.to_numeric(qbs['Depth'], errors='coerce')
        depth1 = qbs[qbs['DepthNumeric'] == 1]
        depth2 = qbs[qbs['DepthNumeric'] == 2]
        if len(depth1) == 0:
            continue
        depth1_idx = depth1.index[0]
        depth1_games = pd.to_numeric(depth1.loc[depth1_idx, 'G'], errors='coerce')
        depth1_games = 0 if pd.isna(depth1_games) else depth1_games
        backup_games = min(3, max(0, 17 - depth1_games))
        qb1_games = 17 - backup_games
        qb1_ratio = qb1_games / 17
        backup_ratio = backup_games / 17
        stat_columns = ['PPR', 'STD', 'PassAtt', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
        PreS.loc[depth1_idx, stat_columns] *= qb1_ratio
        for idx in depth2.index:
            PreS.loc[idx, stat_columns] *= backup_ratio

    PreS.iloc[:, 3:] = PreS.iloc[:, 3:].apply(pd.to_numeric, errors='coerce').round(1)
    return PreS


def PreSdataframe(useful, teamtotals, week, schedule):
    statcolumns = ['Player', 'Team', 'Pos.', 'Age', 'PPR', 'STD', 'PassAtt', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    PreS = pd.DataFrame()
    PreS['Player'] = useful['Player']
    PreS['Team'] = useful['Team']
    PreS['Pos.'] = useful['Pos.']
    PreS['Age'] = useful['Age']
    for stat in statcolumns[4:]:
        PreS[stat] = 0.0
    n_simulations = 10000
    team_stats = teamtotals.set_index('Team').to_dict('index')
    for current_week in range(week, 18):
        predictedrushes = []
        predictedrushyards = []
        predictedrushtds = []
        predictedreceptions = []
        predictedreceivingyards = []
        predictedreceivingtds = []
        predictedpassingattempts = []
        predictedpassingyards = []
        predictedpassingtds = []
        predictedints = []
        pprs = []
        stds = []
        schedule_map = {row[0]: row[current_week] for row in schedule.itertuples(index=False)}
        for i, row in useful.iterrows():
            player_team = row['Team']
            opp = schedule_map.get(player_team, 'BYE')
            randoms = np.random.uniform(-2, 2, (18, n_simulations))
            if opp == 'BYE':
                rushes = np.zeros(n_simulations)
                rushyards = np.zeros(n_simulations)
                rushtds = np.zeros(n_simulations)
                receptions = np.zeros(n_simulations)
                receivingyards = np.zeros(n_simulations)
                receivingtds = np.zeros(n_simulations)
                passingattempts = np.zeros(n_simulations)
                passingyards = np.zeros(n_simulations)
                passingtds = np.zeros(n_simulations)
                ints = np.zeros(n_simulations)
            else:
                opponent = team_stats.get(opp, {})
                rush_attempt_adjustment = opponent.get('RushAttAAV', 0) * row['Rush%']
                rushes = row['RushAttperGame'] + row['RushStDev'] * randoms[0] * (1 + rush_attempt_adjustment * opponent.get('RushAttAAVStDev', 0) * randoms[1])
                rushes = np.clip(rushes, 0, None)
                rush_yards_per_att = row['RushYdsperAtt'] + row['RushYdsperAttStDev'] * randoms[2]
                rushyards = rushes * np.clip(rush_yards_per_att, 0, None)
                rush_td_per_att = row['RushTDperAtt'] + row['RushTDperAttStDev'] * randoms[3]
                rushtds = rushes * np.clip(rush_td_per_att, 0, None)
                rec_adjustment = opponent.get('RecAAV', 0) * row['Rec%']
                receptions = row['RecperGame'] + row['RecStDev'] * randoms[4] * (1 + rec_adjustment * opponent.get('RecAAVStDev', 0) * randoms[5])
                receptions = np.clip(receptions, 0, None)
                rec_yards_per_att = row['RecYdsperAtt'] + row['RecYdsperAttStDev'] * randoms[6]
                receivingyards = receptions * np.clip(rec_yards_per_att, 0, None)
                rec_td_per_att = row['RecTDperAtt'] + row['RecTDperAttStDev'] * randoms[7]
                receivingtds = receptions * np.clip(rec_td_per_att, 0, None)
                pass_attempt_adjustment = opponent.get('PassAttAAV', 0)
                passingattempts = row['PassAttperGame'] + row['PassAttStDev'] * randoms[8] * (1 + pass_attempt_adjustment * opponent.get('PassAttAAVStDev', 0) * randoms[9])
                passingattempts = np.clip(passingattempts, 0, None)
                pass_yards_per_att = row['PassYdsperAtt'] + row['PassYdsperAttStDev'] * randoms[10]
                passingyards = passingattempts * np.clip(pass_yards_per_att, 0, None)
                pass_td_per_att = row['PassTDperAtt'] + row['PassTDperAttStDev'] * randoms[11]
                passingtds = passingattempts * np.clip(pass_td_per_att, 0, None)
                int_per_att = row['IntperAtt'] + row['IntperAttStDev'] * randoms[12]
                ints = passingattempts * np.clip(int_per_att, 0, None)
            rushes_mean = int(np.round(np.nanmean(np.nan_to_num(rushes, nan=0))))
            rushyards_mean = int(np.round(np.nanmean(np.nan_to_num(rushyards, nan=0))))
            rushtds_mean = np.round(np.nanmean(np.nan_to_num(rushtds, nan=0)), 1)
            receptions_mean = int(np.round(np.nanmean(np.nan_to_num(receptions, nan=0))))
            receivingyards_mean = int(np.round(np.nanmean(np.nan_to_num(receivingyards, nan=0))))
            receivingtds_mean = np.round(np.nanmean(np.nan_to_num(receivingtds, nan=0)), 1)
            passingattempts_mean = int(np.round(np.nanmean(np.nan_to_num(passingattempts, nan=0))))
            passingyards_mean = int(np.round(np.nanmean(np.nan_to_num(passingyards, nan=0))))
            passingtds_mean = np.round(np.nanmean(np.nan_to_num(passingtds, nan=0)), 1)
            ints_mean = np.round(np.nanmean(np.nan_to_num(ints, nan=0)), 1)
            predictedrushes.append(rushes_mean)
            predictedrushyards.append(rushyards_mean)
            predictedrushtds.append(rushtds_mean)
            predictedreceptions.append(receptions_mean)
            predictedreceivingyards.append(receivingyards_mean)
            predictedreceivingtds.append(receivingtds_mean)
            predictedpassingattempts.append(passingattempts_mean)
            predictedpassingyards.append(passingyards_mean)
            predictedpassingtds.append(passingtds_mean)
            predictedints.append(ints_mean)
            ppr = rushyards_mean / 10 + receivingyards_mean / 10 + passingyards_mean / 25 + receptions_mean + (rushtds_mean + receivingtds_mean) * 6 + passingtds_mean * 4
            std = rushyards_mean / 10 + receivingyards_mean / 10 + passingyards_mean / 25 + (rushtds_mean + receivingtds_mean) * 6 + passingtds_mean * 4
            pprs.append(ppr)
            stds.append(std)
        PreS['RushAtt'] += predictedrushes
        PreS['RushYds'] += predictedrushyards
        PreS['RushTD'] += predictedrushtds
        PreS['Rec'] += predictedreceptions
        PreS['RecYds'] += predictedreceivingyards
        PreS['RecTD'] += predictedreceivingtds
        PreS['PassAtt'] += predictedpassingattempts
        PreS['PassYds'] += predictedpassingyards
        PreS['PassTD'] += predictedpassingtds
        PreS['Int'] += predictedints
        PreS['PPR'] += pprs
        PreS['STD'] += stds
    for team, team_df in useful.groupby('Team'):
        qbs = team_df[team_df['Pos.'] == 'QB'].copy()
        qbs['DepthNumeric'] = pd.to_numeric(qbs['Depth'], errors='coerce')
        depth1 = qbs[qbs['DepthNumeric'] == 1]
        depth2 = qbs[qbs['DepthNumeric'] == 2]
        if len(depth1) == 0:
            continue
        depth1_idx = depth1.index[0]
        depth1_games = pd.to_numeric(depth1.loc[depth1_idx, 'G'], errors='coerce')
        depth1_games = 0 if pd.isna(depth1_games) else depth1_games
        backup_games = min(3, max(0, 17 - depth1_games))
        qb1_games = 17 - backup_games
        qb1_ratio = qb1_games / 17
        backup_ratio = backup_games / 17
        stat_columns = ['PPR', 'STD', 'PassAtt', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
        PreS.loc[depth1_idx, stat_columns] *= qb1_ratio
        for idx in depth2.index:
            PreS.loc[idx, stat_columns] *= backup_ratio
    PreS.iloc[:, 3:] = PreS.iloc[:, 3:].apply(pd.to_numeric, errors='coerce').round(1)
    return PreS


def PreSdataframe0(useful, teamtotals, week, schedule):
    statcolumns = ['Player', 'Team', 'Pos.', 'Age', 'PPR', 'STD', 'PassAtt', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    PreS = pd.DataFrame()
    PreS['Player'] = useful['Player']
    PreS['Team'] = useful['Team']
    PreS['Pos.'] = useful['Pos.']
    PreS['Age'] = useful['Age']
    for stat in statcolumns[4:]:
        PreS[stat] = 0.0
    n_simulations = 10000
    team_stats = teamtotals.set_index('Team').to_dict('index')
    for current_week in range(week, 18):
        predictedrushes = []
        predictedrushyards = []
        predictedrushtds = []
        predictedreceptions = []
        predictedreceivingyards = []
        predictedreceivingtds = []
        predictedpassingattempts = []
        predictedpassingyards = []
        predictedpassingtds = []
        predictedints = []
        pprs = []
        stds = []
        schedule_map = {row[0]: row[current_week] for row in schedule.itertuples(index=False)}
        for i, row in useful.iterrows():
            player_team = row['Team']
            opp = schedule_map.get(player_team, 'BYE')
            randoms = np.random.uniform(-2, 2, (18, n_simulations))
            if opp == 'BYE':
                rushes = np.zeros(n_simulations)
                rushyards = np.zeros(n_simulations)
                rushtds = np.zeros(n_simulations)
                receptions = np.zeros(n_simulations)
                receivingyards = np.zeros(n_simulations)
                receivingtds = np.zeros(n_simulations)
                passingattempts = np.zeros(n_simulations)
                passingyards = np.zeros(n_simulations)
                passingtds = np.zeros(n_simulations)
                ints = np.zeros(n_simulations)
            else:
                team = team_stats.get(opp, {})
                games = pd.to_numeric(row['G'], errors='coerce')
                games = 0 if pd.isna(games) else games
                if games > 0:
                    rushes = (row['RushAtt'] / games) + row['RushStDev'] * randoms[0] * (1 + team.get('RushAttAAV', 0) * row['Rush%'] * team.get('RushAttAAVStDev', 0) * randoms[1])
                    rushyards = (row['RushYds'] / games) + row['RushYdsStDev'] * randoms[2] * (1 + team.get('RushYdsAAV', 0) * row['RushYds%'] * team.get('RushYdsAAVStDev', 0) * randoms[3])
                    rushtds = (row['RushTD'] / games) + row['RushTDStDev'] * randoms[4] * (1 + team.get('RushTDAAV', 0) * row['RushTD%'] * team.get('RushTDAAVStDev', 0) * randoms[5])
                    receptions = row['RecperGame'] + row['RecStDev'] * randoms[6] * (1 + team.get('RecAAV', 0) * row['Rec%'] * team.get('RecAAVStDev', 0) * randoms[7])
                    receivingyards = (row['RecYds'] / games) + row['RecYdsStDev'] * randoms[8] * (1 + team.get('RecYdsAAV', 0) * row['RecYds%'] * team.get('RecYdsAAVStDev', 0) * randoms[9])
                    receivingtds = (row['RecTD'] / games) + row['RecTDStDev'] * randoms[10] * (1 + team.get('RecTDAAV', 0) * row['RecTD%'] * team.get('RecTDAAVStDev', 0) * randoms[11])
                    passingattempts = row['PassAttperGame'] + row['PassAttStDev'] * randoms[12] * (1 + team.get('PassAttAAV', 0) * row['PassAtt%'] * team.get('PassAttAAVStDev', 0) * randoms[13])
                    passingyards = (row['PassYds'] / games) + row['PassYdsStDev'] * randoms[14] * (1 + team.get('PassYdsAAV', 0) * row['PassYds%'] * team.get('PassYdsAAVStDev', 0) * randoms[15])
                    passingtds = (row['PassTD'] / games) + row['PassTDStDev'] * randoms[16] * (1 + team.get('PassTDAAV', 0) * row['PassTD%'] * team.get('PassTDAAVStDev', 0) * randoms[17])
                    ints = (row['Int'] / games) + row['IntStDev'] * randoms[18] * (1 + team.get('IntAAV', 0) * row['Int%'] * team.get('IntAAVStDev', 0) * randoms[19])
                    rushes = np.clip(rushes, 0, None)
                    rushyards = np.clip(rushyards, 0, None)
                    rushtds = np.clip(rushtds, 0, None)
                    receptions = np.clip(receptions, 0, None)
                    receivingyards = np.clip(receivingyards, 0, None)
                    receivingtds = np.clip(receivingtds, 0, None)
                    passingattempts = np.clip(passingattempts, 0, None)
                    passingyards = np.clip(passingyards, 0, None)
                    passingtds = np.clip(passingtds, 0, None)
                    ints = np.clip(ints, 0, None)
                else:
                    rushes = np.zeros(n_simulations)
                    rushyards = np.zeros(n_simulations)
                    rushtds = np.zeros(n_simulations)
                    receptions = np.zeros(n_simulations)
                    receivingyards = np.zeros(n_simulations)
                    receivingtds = np.zeros(n_simulations)
                    passingattempts = np.zeros(n_simulations)
                    passingyards = np.zeros(n_simulations)
                    passingtds = np.zeros(n_simulations)
                    ints = np.zeros(n_simulations)
            rushes_mean = int(np.round(np.nanmean(np.nan_to_num(rushes, nan=0))))
            rushyards_mean = int(np.round(np.nanmean(np.nan_to_num(rushyards, nan=0))))
            rushtds_mean = np.round(np.nanmean(np.nan_to_num(rushtds, nan=0)), 1)
            receptions_mean = int(np.round(np.nanmean(np.nan_to_num(receptions, nan=0))))
            receivingyards_mean = int(np.round(np.nanmean(np.nan_to_num(receivingyards, nan=0))))
            receivingtds_mean = np.round(np.nanmean(np.nan_to_num(receivingtds, nan=0)), 1)
            passingattempts_mean = int(np.round(np.nanmean(np.nan_to_num(passingattempts, nan=0))))
            passingyards_mean = int(np.round(np.nanmean(np.nan_to_num(passingyards, nan=0))))
            passingtds_mean = np.round(np.nanmean(np.nan_to_num(passingtds, nan=0)), 1)
            ints_mean = np.round(np.nanmean(np.nan_to_num(ints, nan=0)), 1)
            predictedrushes.append(rushes_mean)
            predictedrushyards.append(rushyards_mean)
            predictedrushtds.append(rushtds_mean)
            predictedreceptions.append(receptions_mean)
            predictedreceivingyards.append(receivingyards_mean)
            predictedreceivingtds.append(receivingtds_mean)
            predictedpassingattempts.append(passingattempts_mean)
            predictedpassingyards.append(passingyards_mean)
            predictedpassingtds.append(passingtds_mean)
            predictedints.append(ints_mean)
            ppr = rushyards_mean / 10 + receivingyards_mean / 10 + passingyards_mean / 25 + receptions_mean + (rushtds_mean + receivingtds_mean) * 6 + passingtds_mean * 4
            std = rushyards_mean / 10 + receivingyards_mean / 10 + passingyards_mean / 25 + (rushtds_mean + receivingtds_mean) * 6 + passingtds_mean * 4
            pprs.append(ppr)
            stds.append(std)
        PreS['RushAtt'] += predictedrushes
        PreS['RushYds'] += predictedrushyards
        PreS['RushTD'] += predictedrushtds
        PreS['Rec'] += predictedreceptions
        PreS['RecYds'] += predictedreceivingyards
        PreS['RecTD'] += predictedreceivingtds
        PreS['PassAtt'] += predictedpassingattempts
        PreS['PassYds'] += predictedpassingyards
        PreS['PassTD'] += predictedpassingtds
        PreS['Int'] += predictedints
        PreS['PPR'] += pprs
        PreS['STD'] += stds
    for team, team_df in useful.groupby('Team'):
        qbs = team_df[team_df['Pos.'] == 'QB'].copy()
        qbs['DepthNumeric'] = pd.to_numeric(qbs['Depth'], errors='coerce')
        depth1 = qbs[qbs['DepthNumeric'] == 1]
        depth2 = qbs[qbs['DepthNumeric'] == 2]
        if len(depth1) == 0:
            continue
        depth1_idx = depth1.index[0]
        depth1_games = pd.to_numeric(depth1.loc[depth1_idx, 'G'], errors='coerce')
        depth1_games = 0 if pd.isna(depth1_games) else depth1_games
        backup_games = min(3, max(0, 17 - depth1_games))
        qb1_games = 17 - backup_games
        qb1_ratio = qb1_games / 17
        backup_ratio = backup_games / 17
        stat_columns = ['PPR', 'STD', 'PassAtt', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
        PreS.loc[depth1_idx, stat_columns] *= qb1_ratio
        for idx in depth2.index:
            PreS.loc[idx, stat_columns] *= backup_ratio
    PreS.iloc[:, 3:] = PreS.iloc[:, 3:].apply(pd.to_numeric, errors='coerce').round(1)
    return PreS


def preseason_prediction_html(dfs):
    for name, df in dfs.items():

        html_string = df.to_html(classes='display', index=False).replace('class="dataframe display"', 'class="display"')
        
        # Full HTML file with sorting and ALL rows shown
        html_script = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title> PreSeason NFL Predictions </title>
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
                <a href="/WebProjects/Preseason_html/All.html">Preseason Predictions</a>
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

        <h1>Preseason Predictions</h1>

        <div class="topnav">
        <input type="text" id="searchBar" placeholder="Search...">
        </div>

                <div class="topnav">
        <a {"class='active'" if name == "All" else ""} href="All.html">All</a>
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
        with open(f"Preseason_html/{name}.html", "w", encoding="utf-8") as f:
            f.write(html_script)
        

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
        total_team_int = 0

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
            team_total_Int = df.loc[df['Team'] == team, 'Int'].sum()

            total_team_completions += team_total_C
            total_team_pass_yards += team_total_PY
            total_team_pass_td += team_total_PT
            total_team_rec += team_total_R
            total_team_rec_yards += team_total_RY
            total_team_rec_td += team_total_RT
            total_team_rush_att += team_total_Ru
            total_team_rush_yards += team_total_RuY
            total_team_rush_td += team_total_RuT
            total_team_int += team_total_Int

        # Save result
        teamtotals.append({'Team': team, 'CmpAAV': total_team_completions, 'PassYdsAAV': total_team_pass_yards, 'PassTDAAV': total_team_pass_td, 'IntAAV': total_team_int, 'RecAAV': total_team_rec, 'RecYdsAAV': total_team_rec_yards, 'RecTDAAV': total_team_rec_td, 'RushAttAAV': total_team_rush_att, 'RushYdsAAV': total_team_rush_yards, 'RushTDAAV': total_team_rush_td})

    TeamTotals = pd.DataFrame(teamtotals)

    #Added Standard deviations to the weekly corrections and turned AAVs into %'s
    for column in TeamTotals.columns[1:]:
        row_index=0

        league_average = TeamTotals[column].mean()
        
        if (df.iloc[row_index, :len(dflist)] == 'BYE').any():
            correction = (TeamTotals[column] - TeamTotals[column].mean())/(len(dflist-1))/league_average
            
        else:
            correction = (TeamTotals[column] - TeamTotals[column].mean())/len(dflist)/league_average

        TeamTotals[column] = correction
        TeamTotals[column + 'StDev'] = correction.std()

    return TeamTotals


def weeklySuperFlexdataframe(useful, teamtotals): #Add Int's to this

    #Simulate 10,000 games and average for predictions
    n_simulations = 10000
    team_stats = teamtotals.set_index('Team').to_dict('index')

    statcolumns = ['Player', 'Team', 'Pos.', 'PPR', 'STD', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
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
    predictedints = []

    pprs = []
    stds = []

    for i, row in useful.iterrows():
        opp = row['Opp']
        randoms = np.random.uniform(-2, 2, (18, n_simulations))

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
            ints = np.zeros(n_simulations)
            
        else:
            team = team_stats[opp]

            # Simulations
            #Left One to see what it used to look like if the new changes bomb
            #rushes = (row['RushAtt'] / row['G']) + row['RushStDev'] * randoms[0] + team['RushAttAAV'] * row['Rush%'] * row['RushAttAAVStDev'] * randoms[1]
            rushes = (row['RushAtt'] / row['G']) + row['RushStDev'] * randoms[0] * (1 + team['RushAttAAV'] * row['Rush%'] * row['RushAttAAVStDev'] * randoms[1])
            rushyards = (row['RushYds'] / row['G']) + row['RushYdsStDev'] * randoms[2] * (1 + team['RushYdsAAV'] * row['RushYds%'] * row['RushYdsAAVStDev'] * randoms[3])
            rushtds = (row['RushTD'] / row['G']) + row['RushTDStDev'] * randoms[4] * (1 + team['RushTDAAV'] * row['RushTD%'] * row['RushTDAAVStDev'] * randoms[5])

            receptions = (row['Tgt'] / row['G']) * row['IndCatch%'] + row['TgtStDev'] * row['IndCatch%']* randoms[6] * (1 + team['RecAAV'] * row['TmCatch%'] * row['RecAAVStDev'] * randoms[7])
            receivingyards = (row['RecYds'] / row['G']) + row['RecYdsStDev'] * randoms[8] * (1 + team['RecYdsAAV'] * row['RecYds%'] * row['RecYdsAAVStDev'] * randoms[9])
            receivingtds = (row['RecTD'] / row['G']) + row['RecTDStDev'] * randoms[10] * (1 + team['RecTDAAV'] * row['RecTD%'] * row['RecTDAAVStDev'] * randoms[11])

            passingyards = (row['PassYds'] / row['G']) + row['PassYdsStDev'] * randoms[12] * (1 + team['PassYdsAAV'] * row['PassYds%'] * row['PassYdsAAVStDev'] * randoms[13])
            passingtds = (row['PassTD'] / row['G']) + row['PassTDStDev'] * randoms[14] * (1 + team['PassTDAAV'] * row['PassTD%'] * row['PassTDAAVStDev'] * randoms[15])
            ints = (row['Int'] / row['G']) + row['IntStDev'] * randoms[16] * (1 + team['IntAAV'] * row['Int%'] * row['IntAAVStDev'] * randoms[17])

        players.append(row['Player'])

        predictedrushes.append(np.clip(np.round(rushes.mean()).astype(int), 0, None))
        predictedrushyards.append(np.clip(np.round(rushyards.mean()).astype(int), 0, None))
        predictedrushtds.append(np.clip(np.round(rushtds.mean(),1), 0, None))

        predictedreceptions.append(np.clip(np.round(receptions.mean()).astype(int), 0, None))
        predictedreceivingyards.append(np.clip(np.round(receivingyards.mean()).astype(int), 0, None))
        predictedreceivingtds.append(np.clip(np.round(receivingtds.mean(),1), 0, None))

        predictedpassingyards.append(np.clip(np.round(passingyards.mean()).astype(int), 0, None))
        predictedpassingtds.append(np.clip(np.round(passingtds.mean(),1), 0, None))
        predictedints.append(np.clip(np.round(ints.mean(),1), 0, None))

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
    SuperFlex['Int'] = predictedints
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
                <a href="/WebProjects/Preseason_html/All.html">Preseason Predictions</a>
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

    statcolumns = ['Player', 'Team', 'Pos.', 'Age', 'PPR', 'STD', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']

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
        predictedints = []

        pprs = []
        stds = []

        schedule_map = {row[0]: row[week] for row in schedule.itertuples(index=False)}
        for i, row in useful.iterrows():

            team = row['Team']
            opp = schedule_map.get(team, 'BYE')
            randoms = np.random.uniform(-2, 2, (18, n_simulations))
            if opp == 'BYE':
                
                rushes = np.zeros(n_simulations)
                rushyards = np.zeros(n_simulations)
                rushtds= np.zeros(n_simulations)

                receptions = np.zeros(n_simulations)
                receivingyards = np.zeros(n_simulations)
                receivingtds = np.zeros(n_simulations)

                passingyards = np.zeros(n_simulations)
                passingtds = np.zeros(n_simulations)
                ints = np.zeros(n_simulations)
                
            else:
                team = team_stats[opp]
                
                # Simulations
                rushes = (row['RushAtt'] / row['G']) + row['RushStDev'] * randoms[0] * (1 + team['RushAttAAV'] * row['Rush%'] * team['RushAttAAVStDev'] * randoms[1])
                rushyards = (row['RushYds'] / row['G']) + row['RushYdsStDev'] * randoms[2] * (1 + team['RushYdsAAV'] * row['RushYds%'] * team['RushYdsAAVStDev'] * randoms[3])
                rushtds = (row['RushTD'] / row['G']) + row['RushTDStDev'] * randoms[4] * (1 + team['RushTDAAV'] * row['RushTD%'] * team['RushTDAAVStDev'] * randoms[5])

                receptions = (row['Tgt'] / row['G']) * row['IndCatch%'] + row['TgtStDev'] * row['IndCatch%']* randoms[6] * (1 + team['RecAAV'] * row['TmCatch%'] * team['RecAAVStDev'] * randoms[7])
                receivingyards = (row['RecYds'] / row['G']) + row['RecYdsStDev'] * randoms[8] * (1 + team['RecYdsAAV'] * row['RecYds%'] * team['RecYdsAAVStDev'] * randoms[9])
                receivingtds = (row['RecTD'] / row['G']) + row['RecTDStDev'] * randoms[10] * (1 + team['RecTDAAV'] * row['RecTD%'] * team['RecTDAAVStDev'] * randoms[11])

                passingyards = (row['PassYds'] / row['G']) + row['PassYdsStDev'] * randoms[12] * (1 + team['PassYdsAAV'] * row['PassYds%'] * team['PassYdsAAVStDev'] * randoms[13])
                passingtds = (row['PassTD'] / row['G']) + row['PassTDStDev'] * randoms[14] * (1 + team['PassTDAAV'] * row['PassTD%'] * team['PassTDAAVStDev'] * randoms[15])
                ints = (row['Int'] / row['G']) + row['IntStDev'] * randoms[16] * (1 + team['IntAAV'] * row['Int%'] * team['IntAAVStDev'] * randoms[17])

            players.append(row['Player'])

            predictedrushes.append(np.clip(int(np.round(np.nanmean(np.nan_to_num(rushes, nan=0)))), 0, None))
            predictedrushyards.append(np.clip(int(np.round(np.nanmean(np.nan_to_num(rushyards, nan=0)))), 0, None))
            predictedrushtds.append(np.clip(np.round(rushtds.mean(),1), 0, None))

            predictedreceptions.append(np.clip(int(np.round(np.nanmean(np.nan_to_num(receptions, nan=0)))), 0, None))
            predictedreceivingyards.append(np.clip(int(np.round(np.nanmean(np.nan_to_num(receivingyards, nan=0)))), 0, None))
            predictedreceivingtds.append(np.clip(np.round(receivingtds.mean(),1), 0, None))

            predictedpassingyards.append(np.clip(int(np.round(np.nanmean(np.nan_to_num(passingyards, nan=0)))), 0, None))
            predictedpassingtds.append(np.clip(np.round(passingtds.mean(),1), 0, None))
            predictedints.append(np.clip(np.round(ints.mean(),1), 0, None))
            

            # Fantasy scoring
            ppr = (
                int(np.round(np.nanmean(np.nan_to_num(rushyards, nan=0)))) / 10 +
                int(np.round(np.nanmean(np.nan_to_num(receivingyards, nan=0)))) / 10 +
                int(np.round(np.nanmean(np.nan_to_num(passingyards, nan=0)))) / 25 +
                int(np.round(np.nanmean(np.nan_to_num(receptions, nan=0)))) +
                (np.round(rushtds.mean(),1) + np.round(receivingtds.mean(),1)) * 6 +
                np.round(passingtds.mean(),1) * 4
            )
            pprs.append(ppr)

            std = (
                int(np.round(np.nanmean(np.nan_to_num(rushyards, nan=0)))) / 10 +
                int(np.round(np.nanmean(np.nan_to_num(receivingyards, nan=0)))) / 10 +
                int(np.round(np.nanmean(np.nan_to_num(passingyards, nan=0)))) / 25 +
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
        ROS['Int'] += predictedints
        ROS['PPR'] += pprs
        ROS['STD'] += stds
        ROS.iloc[:, 3:5] = ROS.iloc[:, 3:5].apply(pd.to_numeric).round(1)

    ROS['Team'] = useful['Team']

    return ROS


def rosfinaldataframes(ros):

    #flexstatcolumns = ['Player', 'Team', 'PPR', 'STD', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    statcolumns = ['Player', 'Team', 'PPR', 'STD', 'PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    Flex_ROS = pd.DataFrame(columns=statcolumns)
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
                <a href="/WebProjects/Preseason_html/All.html">Preseason Predictions</a>
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
                <a href="/WebProjects/Preseason_html/All.html">Preseason Predictions</a>
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
        elif passatt != 0 and totalpasstds + totalrectds + totalrushtds != 0:
            QBDom.at[i, 'Off Focus'] = round(passyds/passatt + passtds + totalpasstds/(totalpasstds + totalrectds + totalrushtds),1)
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
                <a href="/WebProjects/Preseason_html/All.html">Preseason Predictions</a>
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
                    <a href="/WebProjects/Preseason_html/All.html">Preseason Predictions</a>
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
        

        <img src="/WebProjects/images/Baseball_Logo.png" alt="Header Image" class="header-img">

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
                <a href="/WebProjects/Preseason_html/All.html">Preseason Predictions</a>
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
        

        <img src="/WebProjects/images/Baseball_Logo.png" alt="Header Image" class="header-img">

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


