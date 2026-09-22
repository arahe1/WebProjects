import subprocess
import sys

scripts = ["Scripts/MLB_predictions.py"]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run([sys.executable, script])