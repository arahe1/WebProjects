import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

listicle = ps.get_nfl_week_files(2025, folder="CSVs")
DFs = ps.importstats(listicle)
Total_Stats = ps.totalstatcombiner(DFs)

age = Total_Stats["Age"].str.split("-", expand=True).astype(float)

Total_Stats["age_decimal"] = age[0] + age[1] / 365.25
Total_Stats["Age"] = (Total_Stats["age_decimal"] * 2).round() / 2

Total_Stats = Total_Stats.drop(columns=["age_decimal"])

age_pos = (Total_Stats.groupby(["Age", "Pos."]).mean(numeric_only=True).reset_index())

Age_Curve = age_pos[["Age", "Pos."]].copy()
Age_Curve["Pass Y/A"] = age_pos["PassYds"] / age_pos["PassAtt"]
Age_Curve["Pass TD/A"] = age_pos["PassTD"] / age_pos["PassAtt"]
Age_Curve["INT/A"] = age_pos["Int"] / age_pos["PassAtt"]

Age_Curve["Rush Y/A"] = age_pos["RushYds"] / age_pos["RushAtt"]
Age_Curve["Rush TD/A"] = age_pos["RushTD"] / age_pos["RushAtt"]

Age_Curve["Y/Rec"] = age_pos["RecYds"] / age_pos["Rec"]
Age_Curve["Rec TD/Rec"] = age_pos["RecTD"] / age_pos["Rec"]



metrics = [
    "Rush Y/A",
    "Pass Y/A",
    "INT/A",
    "Pass TD/A",
    "Y/Rec",
    "Rush TD/A",
    "Rec TD/Rec"
]

curves = {}

for pos in Age_Curve["Pos."].unique():
    curves[pos] = {}

    for metric in metrics:
        data = Age_Curve[
            Age_Curve["Pos."] == pos
        ][["Age", metric]].dropna()

        if len(data) >= 3:
            curves[pos][metric] = np.polyfit(
                data["Age"],
                data[metric],
                2
            )

for pos in curves:
    for metric in curves[pos]:

        ages = np.linspace(20, 45, 200)
        values = np.polyval(curves[pos][metric], ages)

        plt.figure(figsize=(8, 5))
        plt.plot(ages, values)
        plt.xlabel("Age")
        plt.ylabel(metric)
        plt.title(f"{pos} {metric} Aging Curve")
        plt.grid(True)
        plt.show()

