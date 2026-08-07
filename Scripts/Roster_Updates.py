import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

listicle = get_nfl_week_files(2025, folder="CSVs")
DFs = ps.importstats(listicle)
prevdepth = build_depth_chart(DFs, 2025)
newrosters = get_preseason_rosters(2026)
Schedule = ps.schedulemaker('CSVs/Schedule_2025.csv')
Week = len(DFs)+1
Total_Stats = ps.totalstatcombiner(DFs)
IndividualTotals = ps.individualtotals(DFs)
Useful = ps.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)
Dominance = ps.analysis(Useful,IndividualTotals)
updated_depth = update_depth_chart(prevdepth, newrosters, off_focus_df)

