from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import numpy as np
import json
import plotly.graph_objects as go

df = pd.read_csv(
    'data/Railroad_Equipment_Accident_Incident.csv',
    delimiter=',',
    low_memory=False
)

fips_codes = pd.read_csv(
    'data/state_fips_master.csv',
    delimiter=',',
)

states_center = pd.read_csv(
    'data/states_center.csv',
    delimiter=',',
)

fips_codes = fips_codes[['fips', 'state_name']].copy()

df['corrected_year'] = np.where(df['YEAR'] > 24.0, 1900 + df['YEAR'], 2000 + df['YEAR'])
df = df.dropna(subset=['Latitude', 'Longitud']).drop_duplicates(subset=['Latitude', 'Longitud'])
df = pd.merge(df, fips_codes, left_on='STATE', right_on='fips').drop('fips', axis=1)


with open('data/us-states.geojson', 'r') as geojson_file:
    us_states = json.load(geojson_file)


app = Dash(__name__, assets_folder='assets')

app.layout = html.Div(
    children=[
        html.H1("Interactive Railroad Accidents by State", style={"textAlign": "center"}),

        dcc.Graph(
            id='crash-map',
            className='graph-container'
        )
    ],
    style={
        "width": "100%",
        "margin": "0",
        "padding": "0",
    }
)

@app.callback(
    Output('crash-map', 'figure'),
    [
        Input('crash-map', 'clickData'),]
)
def figure(click_data):
    if not click_data:
        zoom = 3
        center = {'lat': 39.8282, 'lon': -98.5795}
    else:
        zoom = 5
        center = {
            'lat': states_center.loc[states_center['Name'] == click_data['points'][0]['location'], 'Latitude'].values[0],
            'lon': states_center.loc[states_center['Name'] == click_data['points'][0]['location'], 'Longitude'].values[0]
        }

    fig = px.choropleth_mapbox(
        geojson=us_states,
        locations=[state['properties']['name'] for state in us_states['features']],
        featureidkey="properties.name",
        hover_name=[state['properties']['name'] for state in us_states['features']],
        color_discrete_sequence=["white"],
        center=center,
        zoom=zoom,
        height=700,
        opacity=0.03
    )

    fig.update_traces(marker_line_color="black", marker_line_width=1)

    fig.update_layout(
        mapbox_style="carto-darkmatter",
        paper_bgcolor='darkgrey',
    )

    if click_data:
        selected_state = click_data['points'][0]['location']
        df_state = df[df['state_name'] == selected_state]

        fig.add_trace(
            go.Scattermapbox(
                lat=df_state['Latitude'],
                lon=df_state['Longitud'],
                mode='markers',
                marker=dict(
                    size=6,
                    color='darkred',
                    opacity=0.5
                ),
                hoverinfo='skip',
            ),
        )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
