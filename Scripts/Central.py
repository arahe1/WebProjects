import subprocess
import sys

scripts = ["Scripts/Weekly_Webpage_Creator.py", "Scripts/Weekly_Scores.py", "Scripts/ROS_Webpage_Creator.py", "Scripts/Dominance.py", "Scripts/MLB_predictions.py", "Scripts/Preseason_Predictions.py"]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run([sys.executable, script])