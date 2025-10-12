import pandas as pd
#import numpy as np
import subprocess
#from collections import defaultdict
#from IPython.display import HTML, display
#import requests
#from bs4 import BeautifulSoup
#import ast
pd.set_option('display.max_columns', None)
from Imports import PYScripts as ps

listicle = ['CSVs/Week_1_NFL_2025.csv','CSVs/Week_2_NFL_2025.csv','CSVs/Week_3_NFL_2025.csv','CSVs/Week_4_NFL_2025.csv','CSVs/Week_5_NFL_2025.csv']
DFs = ps.importstats(listicle)
Schedule = ps.schedulemaker('CSVs/Schedule_2025.csv')
Week = len(DFs)+1
Total_Stats = ps.totalstatcombiner(DFs)
IndividualTotals = ps.individualtotals(DFs)
Useful = ps.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)
Useful = ps.injuryremoval(Useful)
TeamTotals = ps.teamtotals(DFs, Schedule)
All_DataFrames = ps.weeklyfinaldataframes(Useful, TeamTotals)
ps.weeklyhtml(All_DataFrames, Week)

commit_msg = f"Adding data and producing predtictions for Week {Week-1}"

try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Git auto-update complete.")
except subprocess.CalledProcessError:
    print("Git command failed (maybe no changes to commit?)")


