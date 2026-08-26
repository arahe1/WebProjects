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

Useful = ps.preseasonuseful(DFs, Total_Stats, IndividualTotals)


useful_totals = (
    Useful.groupby(["Team", "Pos."])
      .sum(numeric_only=True)
      .reset_index()
)

useful_totals["Team"] = useful_totals["Team"].replace({"WAS": "WSH"})
    

Useful = Useful.drop(columns=["Team"])
Useful = Useful.drop(columns=["Pos."])
Useful = Useful.drop(columns=["Age"])

Useful = depth_chart.merge(Useful, on="Player", how="left")
Useful = ps.standardize_player_names(Useful)

Useful = ps.apply_depth_limits(Useful)
Useful = ps.designate_rookies(Useful)
Useful = ps.assign_rookie_rates(Useful)
Useful = ps.adjust_rookie_percentages(Useful)
Useful = ps.adjust_qb_role_changes(Useful)
#Useful = ps.limit_preseason_tds(Useful, useful_totals)

TeamTotals = ps.teamtotals(DFs, Schedule)
#Useful =  ps.preseason_adjustments(Useful)

print(Useful.loc[Useful['Player'] == 'Michael Wilson', 'RecTDperAtt'].iloc[0])
PreS = ps.PreSdataframe(Useful, TeamTotals, Week, Schedule)
print(PreS.loc[PreS['Player'] == 'Michael Wilson', 'RecTD'].iloc[0])




PreS = PreS.round()
dupes = PreS.loc[PreS["Player"].duplicated(keep=False), "Player"].unique()
#print(dupes)

PreS = ps.balance_passing_receiving(PreS)
print(PreS.loc[PreS['Player'] == 'Michael Wilson', 'RecTD'].iloc[0])

All_DataFrames = ps.rosfinaldataframes(PreS)

df = All_DataFrames['Rest Of Season']
print(df.loc[df['Player'] == 'Michael Wilson', 'RecTD'].iloc[0])

df = ps.standardize_player_names(df) 

df = df.apply(ps.age_adjust_projections, axis=1, curves=curves)
print(df.loc[df['Player'] == 'Michael Wilson', 'RecTD'].iloc[0])

df = df.round()

df = df.drop(columns=["PPR"])
df = df.drop(columns=["STD"])

df = ps.add_fantasy_points(df)

cols = df.select_dtypes(include="number").columns
df[cols] = df[cols].clip(lower=0)

dfs = ps.split_df_by_position(df) 

full_path = os.path.join('CSVs', 'PreSeason_2026.csv')
df.to_csv(full_path, index=False)

ps.preseason_prediction_html(dfs)

with open("Preseason_2026.md", "w", encoding="utf-8") as f:
    df.to_markdown(buf=f, index=False)

print("Preseason Finished")


