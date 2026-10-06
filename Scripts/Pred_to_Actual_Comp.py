import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

df1 = pd.read_csv("CSVs/SuperFlex.csv")
df2 = pd.read_csv("CSVs/Week_4_NFL_2026.csv", sep=",", quoting=3)
df2 = df2.rename(columns={"Att.1": "RushAtt", "Yds": "PassYds","TD": "PassTD","Yds.2": "RushYds","TD.1": "RushTD","Yds.3": "RecYds","TD.2": "RecTD"})

stats = ['PassYds', 'PassTD', 'Int', 'Rec', 'RecYds', 'RecTD', 'RushAtt', 'RushYds', 'RushTD']
merged = df1[["Player", "Pos."] + stats].merge(df2[["Player", "Pos."] + stats], on="Player", suffixes=("_df1", "_df2"))

position_stats = {
    "QB": ["PassYds", "PassTD", "Int", "RushAtt", "RushYds", "RushTD"],
    "RB": ["RushAtt", "RushYds", "RushTD", "Rec", "RecYds", "RecTD"],
    "WR": ["Rec", "RecYds", "RecTD", "RushAtt", "RushYds", "RushTD"],
    "TE": ["Rec", "RecYds", "RecTD", "RushAtt", "RushYds", "RushTD"]
}

cols = ["PassYds_pct_diff", "PassTD_pct_diff", "Int_pct_diff", "Rec_pct_diff", "RecYds_pct_diff", "RecTD_pct_diff", "RushAtt_pct_diff", "RushYds_pct_diff", "RushTD_pct_diff"]

positions = sorted(df1["Pos."].dropna().unique())
results = []

results = []

for pos, stats_for_pos in position_stats.items():
    pos_data = merged[merged["Pos._df1"] == pos]

    for stat in stats_for_pos:
        pred = pos_data[f"{stat}_df1"]
        actual = pos_data[f"{stat}_df2"]
        error = pred - actual

        result = {
            "Pos": pos,
            "Stat": stat,
            "MAE": error.abs().mean(),
            "Bias": error.mean(),
            "RMSE": (error ** 2).mean() ** 0.5,
            "Exact": (pred.round() == actual).mean() * 100,
            "Within1": (abs(pred.round() - actual) <= 1).mean() * 100

        }

        if stat in ["PassTD", "Int", "RecTD", "RushTD"]:
            predicted_event = pred.round() > 0
            actual_event = actual > 0

            tp = (predicted_event & actual_event).sum()
            fp = (predicted_event & ~actual_event).sum()
            fn = (~predicted_event & actual_event).sum()

            precision = tp / (tp + fp) if tp + fp else 0
            recall = tp / (tp + fn) if tp + fn else 0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

            result["Precision"] = precision * 100
            result["Recall"] = recall * 100
            result["F1"] = f1 * 100

        results.append(result)

position_results = pd.DataFrame(results)




with open("Model_Results_Week_4.md", "w") as f:
    for pos in position_results["Pos"].unique():
        f.write(f"# {pos}\n\n")
        f.write(position_results[position_results["Pos"] == pos].to_markdown(index=False))
        f.write("\n\n")










