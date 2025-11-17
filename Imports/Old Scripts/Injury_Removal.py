import requests
from bs4 import BeautifulSoup

def injuryremoval(useful):
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

    useful = useful[~useful['Player'].isin(IR_Players)]
    #SuperFlex = SuperFlex[~SuperFlex['Player'].isin(IR_Players)]
    #Flex = Flex[~Flex['Player'].isin(IR_Players)]
    #WR = WR[~WR['Player'].isin(IR_Players)]
    #RB = RB[~RB['Player'].isin(IR_Players)]
    #TE = TE[~TE['Player'].isin(IR_Players)]
    #QB = QB[~QB['Player'].isin(IR_Players)]

    return useful

