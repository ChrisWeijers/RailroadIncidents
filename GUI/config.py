from GUI.data import get_data
from shapely.geometry import Polygon, box, mapping

df, states_center, state_count, us_states, states_alphabetical, df_map, city_data, crossing_data = get_data()


date_min = df['corrected_year'].min()
date_max = df['corrected_year'].max()

attributes = df.columns

month_min = int(df['IMO'].min())
month_max = int(df['IMO'].max())

damage_min = df['ACCDMG'].min()
damage_max = 35000000

injuries_min = df['TOTINJ'].min()
injuries_max = 400

speed_min = df['TRNSPD'].min()
speed_max = df['TRNSPD'].max()

config = states_alphabetical

# A rough polygon for the U.S. (including Alaska and Hawaii)
US_POLYGON = Polygon([
    (-179.15, 71.39),  # Top-left (Alaska)
    (-130, 50),        # Approx west-coast mainland
    (-125, 30),        # South-west coast
    (-105, 25),        # Southern mainland
    (-80, 25),         # Florida
    (-65, 45),         # North-east coast
    (-75, 50),         # Near New England
    (-100, 60),        # Mid-west to Alaska
    (-179.15, 71.39)   # Close the loop
])

WORLD_BOUNDS = box(-180, -90, 180, 90)
MASK_POLYGON = WORLD_BOUNDS.difference(US_POLYGON)
mask_geojson = mapping(MASK_POLYGON)