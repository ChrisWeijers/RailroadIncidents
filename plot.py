import pandas as pd
import plotly.express as px
import numpy as np
import geopandas as gpd

df = pd.read_csv(
    'data/Railroad_Equipment_Accident_Incident.csv',
    delimiter=',',
    low_memory=False
)

df['corrected_year'] = np.where(df['YEAR'] > 24.0, 1900+df['YEAR'], 2000+df['YEAR'])

df_points = df[['Longitud', 'Latitude']].dropna()

fig = px.scatter_mapbox(
    df,
    lat='Latitude',
    lon='Longitud',
    color_discrete_sequence=['darkred'],
    mapbox_style='carto-darkmatter',
    opacity=0.3,
    zoom=3,
    center={'lat': 39.8282, 'lon': -98.5795},
    template='plotly_dark'
)

fig.update_layout(
    title='Railroad Crashes',
    margin={"r":0,"t":0,"l":0,"b":0},
    autosize=True,
)

fig.update_traces(hoverinfo='skip', hovertemplate=None)

fig.show()