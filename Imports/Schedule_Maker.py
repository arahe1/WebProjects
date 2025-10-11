import pandas as pd
import os

def schedulemaker(csv):
    if not isinstance(csv, str):
        raise TypeError(f"Input should be a CSV path to file name as a string. Got {type(csv)}: {csv}")
    if not csv.lower().endswith('.csv'):
        raise ValueError(f"File is not a CSV file: {csv}")
    if not os.path.exists(csv):
        raise ValueError(f"File not found: {csv}")
    
    #NFL Schedule
    Schedule = pd.read_csv(csv)
    Schedule = Schedule.map(lambda x: x.replace('@', '') if isinstance(x, str) else x)

    #Conform to Stathead Labels
    Schedule = Schedule.map(lambda x: x.replace('GB', 'GNB') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('KC', 'KAN') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('LV', 'LVR') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('NO', 'NOR') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('NE', 'NWE') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('SF', 'SFO') if isinstance(x, str) else x)
    Schedule = Schedule.map(lambda x: x.replace('TB', 'TAM') if isinstance(x, str) else x)
    return Schedule