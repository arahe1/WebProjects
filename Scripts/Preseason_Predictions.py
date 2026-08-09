import pandas as pd
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

depth_chart = pd.read_csv("CSVs/Preseason_Depthchart_2026.csv")

Useful = ps.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)

Useful = Useful.drop(columns=["Team"])
Useful = Useful.drop(columns=["Pos."])

Useful = depth_chart.merge(
    Useful,
    on="Player",
    how="left"
)

TeamTotals = ps.teamtotals(DFs, Schedule)
ROS = ps.ROSdataframe(Useful, TeamTotals, Week, Schedule)
All_DataFrames = ps.rosfinaldataframes(ROS)

df = All_DataFrames['Rest Of Season']

df = df.drop(columns=["PPR"])
df = df.drop(columns=["STD"])

df = df.merge(
    depth_chart[["Player", "Depth"]],
    on="Player",
    how="left"
)

multipliers = {
    1: 1.00,
    2: 0.60,
    3: 0.30,
    4: 0.10,
    5: 0.10,
    6: 0.10,
    7: 0.10,
    8: 0.10,
    9: 0.10,
    10: 0.10,
    11: 0.10,
    12: 0.10,
    13: 0.10,
    14: 0.10,
    15: 0.10,
    16: 0.10,
    17: 0.10,
    18: 0.10,
    19: 0.10,
    20: 0.10
}

for depth, multiplier in multipliers.items():
    df.loc[
        df["Depth"] == depth,
        ["PassYds","PassTD","Rec","RecYds","RecTD","RushAtt","RushYds","RushTD"]
    ] *= multiplier

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


df = ps.assign_remaining_stats_by_position(team_totals, team_totals_future, df)

cols = df.select_dtypes(include="number").columns
df[cols] = df[cols].clip(lower=0)

full_path = os.path.join('CSVs', 'PreSeason_2026.csv')
df.to_csv(full_path, index=False)

team_totals = team_totals.drop(columns=["Age", "Exp", "Depth", "Week", "IndComp%", "TeamComp%", "PassYds%", "PassTD%", "IndCatch%", "TmCatch%", "RecYds%", "RecTD%", "Rush%", "RushYds%", "RushTD%"])

with open("Team_Totals.md", "w", encoding="utf-8") as f:
    team_totals.to_markdown(buf=f, index=False)

with open("Team_Totals_Future.md", "w", encoding="utf-8") as f:
    team_totals_future.to_markdown(buf=f, index=False)

with open("Preseason_2026.md", "w", encoding="utf-8") as f:
    df.to_markdown(buf=f, index=False)
