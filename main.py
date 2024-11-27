import plotly.express as px
import pandas as pd
import json

df = pd.read_csv(
    'data/Railroad_Equipment_Accident_Incident.csv',
    delimiter=',',
    low_memory=False
)

fips_codes = pd.read_csv(
    'data/state_fips_master.csv',
    delimiter=',',
)
fips_codes = fips_codes[['fips', 'state_name']].copy()

df = pd.merge(df, fips_codes, left_on='STATE', right_on='fips').drop('fips', axis=1)

print(df.head())

with open('data/us-states.geojson', 'r') as geojson_file:
    us_states = json.load(geojson_file)

state_count = df.groupby('state_name').size().reset_index(name='crash_count')

fig = px.choropleth(state_count, geojson=us_states, color="crash_count",
                    locations="state_name", featureidkey="properties.name",
                    projection="mercator"
                   )
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0},
    paper_bgcolor='darkgrey',
    plot_bgcolor='darkgrey'
)
fig.show()
