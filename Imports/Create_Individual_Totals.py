import pandas as pd

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

    # Loop through each player in Useful
    for player in unique_names_list:
        total_team_pass_att = 0  # Total sum across all DataFrames
        total_team_pass_yards = 0
        total_team_pass_td = 0
        total_team_rec = 0
        total_team_rec_yards = 0
        total_team_rec_td = 0
        total_team_rush_att = 0
        total_team_rush_yards = 0
        total_team_rush_td = 0

        for df in dflist:
            if player in df['Player'].values:
                # Get the player's team (assumes 1 team per player per df)
                player_team = df.loc[df['Player'] == player, 'Team'].iloc[0]
                #latest_df_with_player = df
                #print(latest_df_with_player.columns)

                # Sum Cmp for all players on the same team
                #player_row = latest_df_with_player[latest_df_with_player['Player'] == player]
                #team_total_PA = latest_df_with_player.loc[latest_df_with_player['Team'] == player_team, 'PassAtt'].sum()
                team_total_PA = df.loc[df['Team'] == player_team, 'PassAtt'].sum()
                team_total_PY = df.loc[df['Team'] == player_team, 'PassYds'].sum()
                team_total_PT = df.loc[df['Team'] == player_team, 'PassTD'].sum()
                team_total_R = df.loc[df['Team'] == player_team, 'Rec'].sum()
                team_total_RY = df.loc[df['Team'] == player_team, 'RecYds'].sum()
                team_total_RT = df.loc[df['Team'] == player_team, 'RecTD'].sum()
                team_total_Ru = df.loc[df['Team'] == player_team, 'RushAtt'].sum()
                team_total_RuY = df.loc[df['Team'] == player_team, 'RushYds'].sum()
                team_total_RuT = df.loc[df['Team'] == player_team, 'RushTD'].sum()

                total_team_pass_att += team_total_PA
                total_team_pass_yards += team_total_PY
                total_team_pass_td += team_total_PT
                total_team_rec += team_total_R
                total_team_rec_yards += team_total_RY
                total_team_rec_td += team_total_RT
                total_team_rush_att += team_total_Ru
                total_team_rush_yards += team_total_RuY
                total_team_rush_td += team_total_RuT

        # Save result
        totals.append({'Player': player, 'TeamTotalPassAtt': total_team_pass_att, 'TeamTotalPassYds': total_team_pass_yards, 'TeamTotalPassTD': total_team_pass_td, 'TeamTotalRec': total_team_rec, 'TeamTotalRecYds': total_team_rec_yards, 'TeamTotalRecTD': total_team_rec_td, 'TeamTotalRushAtt': total_team_rush_att, 'TeamTotalRushYds': total_team_rush_yards, 'TeamTotalRushTD': total_team_rush_td})

    # Create the final result DataFrame
    IndividualTotals = pd.DataFrame(totals)
    return IndividualTotals