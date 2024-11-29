#%%
import pandas as pd
from typing import Tuple, Optional
from math import ceil, floor
import numpy as np
import csv, random

#%%
data = 'data/Rail_Mileposts_20241126.csv'
incident_data = 'data/Railroad_Equipment_Accident_Incident.csv'
df = pd.read_csv(data)

df_incident = pd.read_csv(incident_data, low_memory=False)

#%%
number_of_railroads = df_incident[['RAILROAD']].nunique()
detailed_railroads = df_incident[['RAILROAD']].value_counts()
modern_railroads = df[['RAILROAD']].value_counts()

missing_analysis = pd.DataFrame({
    'Total_Records': df_incident.groupby('RAILROAD').size(),
    'Missing_Latitude': df_incident.groupby('RAILROAD')['Latitude'].apply(lambda x: x.isna().sum()),
    'Missing_Longitude': df_incident.groupby('RAILROAD')['Longitud'].apply(lambda x: x.isna().sum())
})

#%%
incident_railroads = set(detailed_railroads.index)
correct_railroads = set(modern_railroads.index)
intercepted_set = incident_railroads & correct_railroads
df_intercept = pd.DataFrame(incident_railroads - intercepted_set).sort_values(by=0, ascending=True)