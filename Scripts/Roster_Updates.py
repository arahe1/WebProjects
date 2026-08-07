import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

listicle = get_nfl_week_files(2025, folder="CSVs")
DFs = ps.importstats(listicle)
prevdepth = build_depth_chart(DFs, 2025)
newrosters = get_preseason_rosters(2026)
Total_Stats = ps.totalstatcombiner(DFs)
IndividualTotals = ps.individualtotals(DFs)
Dominance = ps.analysis(Total_Stats,IndividualTotals)['FlexDom']
updated_depth = update_depth_chart(prevdepth, newrosters, Dominance)

updated_depth.to_csv("Preseason_DepthChart_2026.csv", index=False)

