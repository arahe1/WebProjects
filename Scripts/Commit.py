import subprocess

commit_msg = input("Please comment on the changes that have been made.")

try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Git auto-update complete.")
except subprocess.CalledProcessError:
    print("Git command failed (maybe no changes to commit?)")