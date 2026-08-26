import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

# Load the CSV file
df = pd.read_csv("CSVs/Preseason_DepthChart_2026.csv")

df = ps.apply_manual_depth_overrides(df)

df.to_csv("CSVs/Preseason_DepthChart_2026.csv", index=False)

print("Rosters and Depth Charts Updated")



