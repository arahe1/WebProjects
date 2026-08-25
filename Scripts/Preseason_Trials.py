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
#print("Arizona RB total rushes:", Useful.loc[(Useful['Team'] == 'ARI') & (Useful['Pos.'] == 'RB'), 'RushAtt'].sum())
#print(Useful.loc[(Useful['Team'] == 'ARI') & (Useful['Pos.'] == 'RB'), ['Player', 'RushAtt', 'RushTD']].to_string(index=False))


TeamTotals = ps.teamtotals(DFs, Schedule)
#Useful =  ps.preseason_adjustments1(Useful)
Useful = Useful.copy().fillna(0)
Useful['G'] = pd.to_numeric(Useful['G'], errors='coerce').fillna(0)
Useful['IsRookie'] = Useful['G'] == 0
Useful = ps.preseason_adjustments_qbs(Useful)
Useful = ps.preseason_adjustments_rbs(Useful)
Useful = ps.preseason_adjustments_wr_te(Useful)
Useful = ps.calculate_preseason_stats(Useful)
Useful = Useful.drop(columns=['IsRookie'])


print("Arizona RB total rushes:", Useful.loc[(Useful['Team'] == 'ARI') & (Useful['Pos.'] == 'RB'), 'RushAtt'].sum())
#print(Useful.loc[(Useful['Team'] == 'ARI') & (Useful['Pos.'] == 'RB'), ['Player', 'RushAtt', 'RushTD']].to_string(index=False))



PreS = ps.PreSdataframe(Useful, TeamTotals, Week, Schedule)
print("Arizona RB total rushes:", PreS.loc[(PreS['Team'] == 'ARI') & (PreS['Pos.'] == 'RB'), 'RushAtt'].sum())
#print(PreS.loc[(PreS['Team'] == 'ARI') & (PreS['Pos.'] == 'RB'), ['Player', 'RushAtt', 'RushTD']].to_string(index=False))

PreS = PreS.round()
dupes = PreS.loc[PreS["Player"].duplicated(keep=False), "Player"].unique()
#print(dupes)

PreS = ps.balance_passing_receiving(PreS)

All_DataFrames = ps.rosfinaldataframes(PreS)


df = All_DataFrames['Rest Of Season']

df = ps.standardize_player_names(df) 

df = df.apply(ps.age_adjust_projections, axis=1, curves=curves)
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


