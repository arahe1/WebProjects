import pandas as pd

def totalstatcombiner(dflist):
    if not isinstance(dflist, list):
        raise TypeError("Expected a List of dataframes Files")
    
    for file in dflist:
        if not isinstance(file, pd.DataFrame):
            raise TypeError(f"List should contain strings of dataframes. Got {type(file)}: {file}")

        
    Combined = pd.concat(dflist, ignore_index=True)
    Numeric_Part = Combined.groupby('Player', as_index=False).sum(numeric_only=True)
    Non_Numeric_Part = Combined.groupby('Player', as_index=False).first(numeric_only=False).drop(columns=Numeric_Part.columns[1:])
    Total_Stats = pd.merge(Numeric_Part, Non_Numeric_Part, on='Player')

    return Total_Stats