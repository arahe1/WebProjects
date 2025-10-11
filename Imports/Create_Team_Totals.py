import pandas as pd

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