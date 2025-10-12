import numpy as np
import pandas as pd

def rosfinaldataframes(useful, teamtotals, week, schedule):

    statcolumns = ['Player', 'Team', 'PPR', 'STD', 'PassYds', 'PassTD', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    Flex_ROS = pd.DataFrame(columns=statcolumns)
    WR_ROS = pd.DataFrame(columns=statcolumns)
    RB_ROS = pd.DataFrame(columns=statcolumns)
    TE_ROS = pd.DataFrame(columns=statcolumns)
    QB_ROS = pd.DataFrame(columns=statcolumns)

    # Prepare your output DataFrame
    ROS = pd.DataFrame()
    ROS['Player'] = useful['Player']

    #Populate Flex with Player names
    for i, row in useful.iterrows():
        keywords = ['WR', 'RB', 'TE']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            Flex_ROS.at[i, 'Player'] = row['Player']

    #Populate WR with Player names
    for i, row in useful.iterrows():
        keywords = ['WR']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            WR_ROS.at[i, 'Player'] = row['Player']

    #Populate RB with Player names
    for i, row in useful.iterrows():
        keywords = ['RB']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            RB_ROS.at[i, 'Player'] = row['Player']

    #Populate TE with Player names
    for i, row in useful.iterrows():
        keywords = ['TE']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            TE_ROS.at[i, 'Player'] = row['Player']

    #Populate QB with Player names
    for i, row in useful.iterrows():
        keywords = ['QB']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            QB_ROS.at[i, 'Player'] = row['Player']

    stats = [col for col in statcolumns if col != 'Player']

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
            rand = np.random.uniform(-2, 2, n_simulations)
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
                rushes = (row['RushAtt'] / row['G']) + row['RushStDev'] * rand + team['RushAttAAV'] * row['Rush%']
                rushyards = (row['RushYds'] / row['G']) + row['RushYdsStDev'] * rand + team['RushYdsAAV'] * row['RushYds%']
                rushtds = (row['RushTD'] / row['G']) + row['RushTDStDev'] * rand + team['RushTDAAV'] * row['RushTD%']

                receptions = (row['Tgt'] / row['G']) * row['IndCatch%'] + row['TgtStDev'] * row['IndCatch%']* rand + team['RecAAV'] * row['TmCatch%']
                receivingyards = (row['RecYds'] / row['G']) + row['RecYdsStDev'] * rand + team['RecYdsAAV'] * row['RecYds%']
                receivingtds = (row['RecTD'] / row['G']) + row['RecTDStDev'] * rand + team['RecTDAAV'] * row['RecTD%']

                passingyards = (row['PassYds'] / row['G']) + row['PassYdsStDev'] * rand + team['PassYdsAAV'] * row['PassYds%']
                passingtds = (row['PassTD'] / row['G']) + row['PassTDStDev'] * rand + team['PassTDAAV'] * row['PassTD%']

            players.append(row['Player'])

            predictedrushes.append(np.round(rushes.mean()).astype(int))
            predictedrushyards.append(np.round(rushyards.mean()).astype(int))
            predictedrushtds.append(np.round(rushtds.mean(),1))

            predictedreceptions.append(np.round(receptions.mean()).astype(int))
            predictedreceivingyards.append(np.round(receivingyards.mean()).astype(int))
            predictedreceivingtds.append(np.round(receivingtds.mean(),1))

            predictedpassingyards.append(np.round(passingyards.mean()).astype(int))
            predictedpassingtds.append(np.round(passingtds.mean(),1))
            

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
        ROS.iloc[:, 2:4] = ROS.iloc[:, 2:4].apply(pd.to_numeric).round(1)

    ROS['Team'] = useful['Team']


    for col in ROS.columns:
        if col != 'Player' and col in Flex_ROS.columns:
            Flex_ROS[col] = Flex_ROS['Player'].map(ROS.set_index('Player')[col])

    for col in ROS.columns:
        if col != 'Player' and col in WR_ROS.columns:
            WR_ROS[col] = WR_ROS['Player'].map(ROS.set_index('Player')[col])

    for col in ROS.columns:
        if col != 'Player' and col in RB_ROS.columns:
            RB_ROS[col] = RB_ROS['Player'].map(ROS.set_index('Player')[col])

    for col in ROS.columns:
        if col != 'Player' and col in TE_ROS.columns:
            TE_ROS[col] = TE_ROS['Player'].map(ROS.set_index('Player')[col])

    for col in ROS.columns:
        if col != 'Player' and col in QB_ROS.columns:
            QB_ROS[col] = QB_ROS['Player'].map(ROS.set_index('Player')[col])

    All_DataFrames = {'Rest Of Season': ROS, 'Flex ROS': Flex_ROS, 'WR ROS': WR_ROS, 'RB ROS': RB_ROS, 'TE ROS': TE_ROS, 'QB ROS': QB_ROS}

    return All_DataFrames



