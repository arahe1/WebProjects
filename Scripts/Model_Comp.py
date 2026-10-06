import pandas as pd

files = [
    "Model_Results_Week_3.md",
    "Model_Results_Week_4.md",
]


def read_markdown_tables(file):
    with open(file, "r") as f:
        lines = f.readlines()

    tables = []
    current_table = []

    for line in lines:
        line = line.strip()

        if line.startswith("|") and line.endswith("|"):
            current_table.append(line)
        elif current_table:
            tables.append(current_table)
            current_table = []

    if current_table:
        tables.append(current_table)

    dfs = []

    for table in tables:
        # Remove markdown separator row
        table = [
            row for row in table
            if not all(
                c.strip().replace("-", "").replace(":", "") == ""
                for c in row.strip("|").split("|")
            )
        ]

        rows = [
            [value.strip() for value in row.strip("|").split("|")]
            for row in table
        ]

        dfs.append(
            pd.DataFrame(
                rows[1:],
                columns=rows[0],
            )
        )

    return dfs


# Load files
dfs = []

for file in files:
    tables = read_markdown_tables(file)

    for df in tables:
        df["Run"] = file
        dfs.append(df)


# Combine
all_stats = pd.concat(dfs, ignore_index=True)


metrics = [
    "MAE",
    "Bias",
    "RMSE",
    "Exact",
    "Within1",
    "Precision",
    "Recall",
    "F1",
]

for metric in metrics:
    all_stats[metric] = pd.to_numeric(
        all_stats[metric],
        errors="coerce",
    )


for metric in metrics:
    table = all_stats.pivot_table(
        index=["Pos", "Stat"],
        columns="Run",
        values=metric,
        sort=False,
    )

output = []

for metric in metrics:
    table = all_stats.pivot_table(
        index=["Pos", "Stat"],
        columns="Run",
        values=metric,
        sort=False,
    )

    output.append(f"# {metric}\n")
    output.append(table.to_markdown())
    output.append("\n")

with open("Model_Comparison.md", "w") as f:
    f.write("\n".join(output))


