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


    for file in files:
            importer = pd.read_csv(file)
            Dataframes.append(importer)


for df in Dataframes:
        df["Pos."] = (df["Pos."].str.replace("\xa0", " ", regex=False).str.strip())
        df["Salary"] = (df["Salary"].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(int))


#with open("Dataframe.md", "w", encoding="utf-8") as f:
#    Dataframe.to_markdown(buf=f, index=False)
def exponential(x, a, b):
    return a * np.exp(-b * x)
parameters = {}
for i, df in enumerate(Dataframes):
    dfs = ps.split_df_by_position(df)
    parameters[i] = {}
    for key, df in dfs.items():
        df["Rank"] = df["Salary"].rank(
            method="min",
            ascending=False
        )

        data = df[["Salary", "Rank"]].dropna()

        if len(data) < 2:
            continue

        y = data["Salary"].values
        x = data["Rank"].values

        params, covariance = curve_fit(
            exponential,
            x,
            y,
            p0=[max(y), 0.05],
            bounds=([0, 0], [np.inf, np.inf]),
            maxfev=10000
        )

        parameters[i][key] = params


#Find values for a specific position
position = "WR"
rank = [8, 17, 24]

# Parameters from your 3 curve fits
a1, k1 = parameters[0][position]
a2, k2 = parameters[1][position]
a3, k3 = parameters[2][position]

# x range
x = np.linspace(0, 20, 500)

# Three fitted curves
y1 = a1 * np.exp(-k1 * x)
y2 = a2 * np.exp(-k2 * x)
y3 = a3 * np.exp(-k3 * x)

# Average curve
y_avg = (y1 + y2 + y3) / 3


salaries = []
salariesranges = []
for ele in rank:
    salary = int(np.round(np.interp(ele, x, y_avg)))
    salary1 = int(a1 * np.exp(-k1 * ele))
    salary2 = int(a2 * np.exp(-k2 * ele))
    salary3 = int(a3 * np.exp(-k3 * ele))
    salariesranges.append([salary1, salary2, salary3])
    salaries.append(salary)

print(salariesranges)
print(salaries)

# Plot
plt.plot(x, y1, '--', alpha=0.5, label='2023')
plt.plot(x, y2, '--', alpha=0.5, label='2024')
plt.plot(x, y3, '--', alpha=0.5, label='2025')

plt.plot(x, y_avg, 'k-', linewidth=3, label='Average curve')

plt.xlabel('Rank')
plt.ylabel('Salary')
plt.legend()
plt.grid()
plt.show()


