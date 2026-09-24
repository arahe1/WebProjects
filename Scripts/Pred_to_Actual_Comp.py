import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

import pandas as pd

df1 = pd.read_csv("CSVs/SuperFlex.csv")
df2 = pd.read_csv("CSVs/Week_2_NFL_2026.csv")
df2 = df2.rename(columns={"Att.1": "RushAtt", "Yds": "PassYds","TD": "PassTD","Yds.2": "RushYds","TD.1": "RushTD","Yds.3": "RecYds","TD.2": "RecTD"})


stats = ['PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']

merged = df1[["Player"] + stats].merge(df2[["Player"] + stats],on="Player",suffixes=("_df1", "_df2"))

for stat in stats:
    merged[f"{stat}_pct_diff"] = ((merged[f"{stat}_df2"] - merged[f"{stat}_df1"])/ merged[f"{stat}_df1"].abs()* 100)

merged = merged.fillna(0).round(2)

merged = merged.loc[:, ~merged.columns.str.endswith(("_df1", "_df2"))]

cols = ["PassYds_pct_diff","RecYds_pct_diff","RushYds_pct_diff"]

for col in cols:
    values = merged[col][merged[col] != 0].abs()
    total = len(values)

    print(f"{col}:")
    print(f"  Under 5%:  {(values < 5).sum() / total * 100:.2f}%")
    print(f"  Under 10%: {(values < 10).sum() / total * 100:.2f}%")
    print(f"  Under 20%: {(values < 20).sum() / total * 100:.2f}%")
    print(f"  Under 50%: {(values < 50).sum() / total * 100:.2f}%")



merged.to_markdown("Percent_Diff.md", index=False)









