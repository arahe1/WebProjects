import pandas as pd
import numpy as np
import subprocess
from collections import defaultdict
from IPython.display import HTML, display
import requests
from bs4 import BeautifulSoup
import ast
pd.set_option('display.max_columns', None)
from Imports import CSV_Importer as ci
from Imports import Schedule_Maker as sm
from Imports import Total_Stats_Combiner as tsc
from Imports import Create_Individual_Totals as cit
from Imports import Create_Useful as cu
from Imports import Create_Team_Totals as ctt
from Imports import Weekly_Final_Dataframes as wfd
from Imports import Create_Weekly_HTML as wrh
from Imports import Injury_Removal as ir

listicle = ['CSVs/Week_1_NFL_2025.csv','CSVs/Week_2_NFL_2025.csv','CSVs/Week_3_NFL_2025.csv','CSVs/Week_4_NFL_2025.csv','CSVs/Week_5_NFL_2025.csv']
DFs = ci.importstats(listicle)
Schedule = sm.schedulemaker('CSVs/Schedule_2025.csv')
Week = len(DFs)+1
Total_Stats = tsc.totalstatcombiner(DFs)
IndividualTotals = cit.individualtotals(DFs)
Useful = cu.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)
Useful = ir.injuryremoval(Useful)
TeamTotals = ctt.teamtotals(DFs, Schedule)
All_DataFrames = wfd.weeklyfinaldataframes(Useful, TeamTotals)
wrh.weeklyhtml(All_DataFrames, Week)

QB = All_DataFrames['QB']
player_row = QB[QB["Player"] == 'Patrick Mahomes']
print(player_row)
print(QB[QB['PassTD'] > 3])

#commit_msg = f"Adding data and producing predtictions for Week {Week-1}"

#try:
#    subprocess.run(["git", "add", "."], check=True)
#    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
#    subprocess.run(["git", "push"], check=True)
#    print("Git auto-update complete.")
#except subprocess.CalledProcessError:
#    print("Git command failed (maybe no changes to commit?)")


