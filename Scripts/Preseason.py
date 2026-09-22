import subprocess
import sys

scripts = ["Scripts/Roster_Updates.py", "Scripts/Preseason_Predictions.py"]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run([sys.executable, script])