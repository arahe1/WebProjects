import pandas as pd
import numpy as np
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps


listicle = ps.get_nfl_week_files(2025, folder="CSVs")
DFs = ps.importstats(listicle) 
Schedule = ps.schedulemaker('CSVs/Schedule_2026.csv')
Week = 1
Total_Stats = ps.totalstatcombiner(DFs)
IndividualTotals = ps.individualtotals(DFs)

Age_Curve, curves = ps.build_age_curves(Total_Stats)

depth_chart = pd.read_csv("CSVs/Preseason_Depthchart_2026.csv")

#Conform to Stathead Labels
depth_chart["Team"] = depth_chart["Team"].replace({
    "GB": "GNB",
    "KC": "KAN",
    "LV": "LVR",
    "NO": "NOR",
    "NE": "NWE",
    "SF": "SFO",
    "TB": "TAM"
})

Useful = ps.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)

useful_totals = (
    Useful.groupby(["Team", "Pos."])
      .sum(numeric_only=True)
      .reset_index()
)

useful_totals["Team"] = useful_totals["Team"].replace({"WAS": "WSH"})

Useful = Useful.drop(columns=["Team"])
Useful = Useful.drop(columns=["Pos."])

Useful = depth_chart.merge(
    Useful,
    on="Player",
    how="left"
)

Useful = ps.standardize_player_names(Useful)

TeamTotals = ps.teamtotals(DFs, Schedule)
ROS = ps.ROSdataframe(Useful, TeamTotals, Week, Schedule)

dupes = ROS.loc[ROS["Player"].duplicated(keep=False), "Player"].unique()
#print(dupes)

All_DataFrames = ps.rosfinaldataframes(ROS)

df = All_DataFrames['Rest Of Season']
df = ps.standardize_player_names(df) 

df = df.drop(columns=["PPR"])
df = df.drop(columns=["STD"])

df = df.merge(
    depth_chart[["Player", "Depth"]],
    on="Player",
    how="left"
)

multipliers = {
    1: 0.90,
    2: 0.60,
    3: 0.30,
    4: 0.10,
    5: 0.05,
    6: 0.05,
    7: 0,
    8: 0,
    9: 0,
    10: 0,
    11: 0,
    12: 0,
    13: 0,
    14: 0,
    15: 0,
    16: 0,
    17: 0,
    18: 0,
    19: 0,
    20: 0
}

for depth, multiplier in multipliers.items():
    mask = df["Depth"] == depth
    df.loc[mask, ["PassYds","PassTD", "Int", "Rec","RecYds","RecTD","RushAtt","RushYds","RushTD"]] = (
        df.loc[mask, ["PassYds","PassTD","Int", "Rec","RecYds","RecTD","RushAtt","RushYds","RushTD"]]
        .astype(float)
        .mul(multiplier)
        .round()
        .fillna(0)
        .replace([np.inf, -np.inf], 0)
        .astype(int)
    )


team_totals = (
    Useful.groupby(["Team", "Pos."])
      .sum(numeric_only=True)
      .reset_index()
)

team_totals_future = (
    df.groupby(["Team", "Pos."])
      .sum(numeric_only=True)
      .reset_index()
)

df = df.apply(ps.age_adjust_projections, axis=1, curves=curves)

df = ps.assign_remaining_stats_by_position(useful_totals, team_totals_future, df)

#df = df.apply(ps.age_adjust_projections, axis=1, curves=curves)

df = df.round(0)

df = ps.add_fantasy_points(df)

cols = df.select_dtypes(include="number").columns
df[cols] = df[cols].clip(lower=0)

dfs = ps.split_df_by_position(df) 

full_path = os.path.join('CSVs', 'PreSeason_2026.csv')
df.to_csv(full_path, index=False)

team_totals = team_totals.drop(columns=["Exp", "Depth", "Week", "IndComp%", "TeamComp%", "PassYds%", "PassTD%", "IndCatch%", "TmCatch%", "RecYds%", "RecTD%", "Rush%", "RushYds%", "RushTD%"])

ps.preseason_prediction_html(dfs)

with open("Useful.md", "w", encoding="utf-8") as f:
    Useful.to_markdown(buf=f, index=False)
    
#with open("Team_Totals.md", "w", encoding="utf-8") as f:
#    team_totals.to_markdown(buf=f, index=False)

#with open("Team_Totals_Future.md", "w", encoding="utf-8") as f:
#    team_totals_future.to_markdown(buf=f, index=False)

with open("Preseason_2026.md", "w", encoding="utf-8") as f:
    df.to_markdown(buf=f, index=False)



print("Preseason Finished")


