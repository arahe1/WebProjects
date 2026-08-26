import pandas as pd
import os
import subprocess
pd.set_option('display.max_columns', None)
from Imports import PyFunc as ps

listicle = ps.get_nfl_week_files(2025, folder="CSVs")
DFs = ps.importstats(listicle)
Schedule = ps.schedulemaker('CSVs/Schedule_2025.csv')
Week = len(DFs)+1
Total_Stats = ps.totalstatcombiner(DFs)
IndividualTotals = ps.individualtotals(DFs)
Useful = ps.usefulstats(DFs, Week, Schedule, Total_Stats, IndividualTotals)
Dominance = ps.analysis(Total_Stats,IndividualTotals)
Dominance = pd.concat([Dominance["QBDom"], Dominance["FlexDom"]], ignore_index=True)
prevdepth = ps.build_depth_chart(Useful, 2025)
newrosters = ps.get_preseason_rosters(2026)
Draft = ps.get_nfl_draft(2026)
updated_depth = ps.update_depth_chart(prevdepth, newrosters, Dominance, Draft)
updated_depth = ps.apply_manual_depth_overrides(updated_depth)
updated_depth = updated_depth[["Team", "Player", "Pos.", "Age", "Exp", "Depth"]]
updated_depth.to_csv("CSVs/Preseason_DepthChart_2026.csv", index=False)

print("Rosters and Depth Charts Updated")



