import numpy as np
from matplotlib.lines import Line2D
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
import matplotlib.pyplot as plt
import sqlite3

df = pd.read_csv(
    'data/Railroad_Equipment_Accident_Incident.csv',
    delimiter=',',
    low_memory=False
)

df['corrected_year'] = np.where(df['YEAR'] > 24.0, 1900+df['YEAR'], 2000+df['YEAR'])

print(df[['Longitud', 'Latitude']].head())
print(sum(df[['Latitude']].isna()))

def plot_rail(data):
    map_railroads = gpd.read_file(r'C:/Users/Cweij/Downloads/USA_Railroads-shp.zip')

    gdf = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in zip(data['Longitud'], data['Latitude'])])
    gdf.crs = map_railroads.crs

    f, ax = plt.subplots(1, figsize=(8, 8))

    map_railroads.plot(linewidth=0.5, edgecolor='white', color='lightgrey', legend=True, ax=ax)
    gdf.plot(ax=ax, marker='o', markersize=10)

    ax.set_title('Railroads', size=15)
    ax.set_xlabel('Longitud')
    ax.set_ylabel('Latitude')

    legend = [
        Line2D([0], [0], markerfacecolor='#FF8F35', marker='o', color='w', label='Weather station'),
        Line2D([0], [0], markerfacecolor='#5499C7', marker='o', color='w', label='Air quality station')
    ]
    ax.legend(handles=legend, loc='upper left')
    return ax

plot_rail(df)
