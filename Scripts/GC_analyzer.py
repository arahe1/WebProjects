import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from Imports import PyFunc as ps
from scipy.optimize import curve_fit
import random

folder="CSVs/GC_Drafts"
files = []
Dataframes=[]
for filename in os.listdir(folder):
    files.append(os.path.join(folder, filename))

    if not isinstance(files, list):
        raise TypeError("Expected a List of CSV Files")

    for file in files:
        if not isinstance(file, str):
            raise TypeError(f"List should contain strings of CSV file names. Got {type(file)}: {file}")
        if not file.lower().endswith('.csv'):
            raise ValueError(f"File is not a CSV file: {file}")
        if not os.path.exists(file):
            raise ValueError(f"File not found: {file}")


#    for file in files:
#            importer = pd.read_csv(file)
#            Dataframes.append(importer)

    Dataframe = pd.concat([pd.read_csv(file) for file in files], ignore_index=True)

#for df in Dataframes:
#        df["Pos."] = (df["Pos."].str.replace("\xa0", " ", regex=False).str.strip())
#        df["Salary"] = (df["Salary"].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(int))
Dataframe["Pos."] = (Dataframe["Pos."].str.replace("\xa0", " ", regex=False).str.strip())
Dataframe["Salary"] = (Dataframe["Salary"].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(int))

dfs = ps.split_df_by_position(Dataframe)

#with open("Dataframe.md", "w", encoding="utf-8") as f:
#    Dataframe.to_markdown(buf=f, index=False)
def exponential(x, a, b):
    return a * np.exp(-b * x)
parameters = {}
for key, df in dfs.items():
    df["Rank"] = df["Salary"].rank(
        method="min",
        ascending=False
    )

    data = df[["Salary", "Rank"]].dropna()

    if len(data) < 2:
        continue

    x = data["Salary"].values
    y = data["Rank"].values

    params, covariance = curve_fit(
        exponential,
        x,
        y,
        p0=[max(y), 0.05],
        bounds=([0, 0], [np.inf, np.inf]),
        maxfev=10000
    )

    parameters[key] = params

print(parameters.keys())
a, b = parameters["WR"]

rank = [8, 25, 36, 23]
for ele in rank:
    salary = -round(np.log(ele / a) / b)

    print(salary)

     
