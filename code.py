import numpy as np
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
import matplotlib.pyplot as plt

df = pd.read_csv(
    'data/Railroad_Equipment_Accident_Incident.csv',
    delimiter=',',
    low_memory=False
)

df['corrected_year'] = np.where(df['YEAR'] > 24.0, 1900+df['YEAR'], 2000+df['YEAR'])

df_points = df[['Longitud', 'Latitude']].dropna()
print(sum(df['Latitude'].isna()))
print(sum(df['Longitud'].isna()))


def create_map(data):
    map_railroads = gpd.read_file(r'USA_Railroads-shp.zip')
    map_states = gpd.read_file(r'cb_2018_us_state_500k.zip')

    gdf = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in zip(data['Longitud'], data['Latitude'])])
    gdf.crs = map_railroads.crs
    gdf.crs = map_states.crs

    return gdf, map_railroads, map_states


gdf, map_railroads, map_states = create_map(df_points)


def plot(gdf, map_railroads, map_states):
    f, ax = plt.subplots(1, figsize=(16, 16))

    f.patch.set_facecolor('black')
    ax.set_facecolor('black')

    map_railroads.plot(linewidth=0.5, edgecolor='white', color='lightgrey', legend=True, ax=ax)
    map_states.plot(linewidth=0.5, edgecolor='white', color='black', legend=True, ax=ax)

    gdf.plot(ax=ax, marker='o', markersize=3)

    ax.set_title('Railroads', size=15)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_xlim(xmin=-130, xmax=-60)
    ax.set_ylim(ymin=20, ymax=55)

    plt.show()
    return ax


plot(gdf, map_railroads, map_states)

