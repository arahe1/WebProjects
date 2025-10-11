import pandas as pd
import numpy as np

def weeklyfinaldataframes(useful, teamtotals):

    #Simulate 10,000 games and average for predictions
    n_simulations = 10000
    team_stats = teamtotals.set_index('Team').to_dict('index')

    statcolumns = ['Player', 'Team', 'PPR', 'STD', 'PassYds', 'PassTD', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
    SuperFlex = pd.DataFrame(columns=statcolumns)
    Flex = pd.DataFrame(columns=statcolumns)
    WR = pd.DataFrame(columns=statcolumns)
    RB = pd.DataFrame(columns=statcolumns)
    TE = pd.DataFrame(columns=statcolumns)
    QB = pd.DataFrame(columns=statcolumns)

    #Populate Superflex with Player names
    SuperFlex['Player'] = useful['Player']
    SuperFlex['Team'] = useful['Team']

    #Populate Flex with Player names
    for i, row in useful.iterrows():
        keywords = ['WR', 'RB', 'TE']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            Flex.at[i, 'Player'] = row['Player']

    #Populate WR with Player names
    for i, row in useful.iterrows():
        keywords = ['WR']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            WR.at[i, 'Player'] = row['Player']

    #Populate RB with Player names
    for i, row in useful.iterrows():
        keywords = ['RB']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            RB.at[i, 'Player'] = row['Player']

    #Populate TE with Player names
    for i, row in useful.iterrows():
        keywords = ['TE']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            TE.at[i, 'Player'] = row['Player']

    #Populate QB with Player names
    for i, row in useful.iterrows():
        keywords = ['QB']
        if any(kw.lower() in row['Pos.'].lower() for kw in keywords):
            QB.at[i, 'Player'] = row['Player']

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
        rand = np.random.uniform(-2, 2, n_simulations)
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
            rushes = (row['RushAtt'] / row['G']) + row['RushStDev'] * rand + team['RushAttAAV'] * row['Rush%']
            rushyards = (row['RushYds'] / row['G']) + row['RushYdsStDev'] * rand + team['RushYdsAAV'] * row['RushYds%']
            rushtds = (row['RushTD'] / row['G']) + row['RushTDStDev'] * rand + team['RushTDAAV'] * row['RushTD%']

            receptions = (row['Tgt'] / row['G']) * row['IndCatch%'] + row['TgtStDev'] * row['IndCatch%'] * rand + team['RecAAV'] * row['TmCatch%']
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
    SuperFlex.iloc[:, 2:4] = SuperFlex.iloc[:, 2:4].apply(pd.to_numeric).round(1)

    for col in SuperFlex.columns:
        if col != 'Player' and col in Flex.columns:
            Flex[col] = Flex['Player'].map(SuperFlex.set_index('Player')[col])

    for col in SuperFlex.columns:
        if col != 'Player' and col in WR.columns:
            WR[col] = WR['Player'].map(SuperFlex.set_index('Player')[col])

    for col in SuperFlex.columns:
        if col != 'Player' and col in RB.columns:
            RB[col] = RB['Player'].map(SuperFlex.set_index('Player')[col])

    for col in SuperFlex.columns:
        if col != 'Player' and col in TE.columns:
            TE[col] = TE['Player'].map(SuperFlex.set_index('Player')[col])

    for col in SuperFlex.columns:
        if col != 'Player' and col in QB.columns:
            QB[col] = QB['Player'].map(SuperFlex.set_index('Player')[col])

    All_DataFrames = {'SuperFlex': SuperFlex, 'Flex': Flex, 'WR': WR, 'RB': RB, 'TE': TE, 'QB': QB}

    return All_DataFrames

