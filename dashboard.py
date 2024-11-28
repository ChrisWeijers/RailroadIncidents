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

state_count = df.groupby('state_name').size().reset_index(name='crash_count').sort_values(by='crash_count',
                                                                                          ascending=False)



app = Dash(__name__, assets_folder='assets')

app.layout = html.Div(
    children=[
        html.H1("Interactive Railroad Accidents by State", style={"textAlign": "center"}),

        dcc.Graph(
            id='crash-map',
            className='graph-container',
            config={
                'scrollZoom': True,       # Enable scroll zoom
                'doubleClick': 'reset',   # Optional: Double-click behavior
                'displayModeBar': True,   # Optional: Show mode bar for additional controls
            },
        ),

        dcc.Graph(id='barchart',
                  className='graph-container')
    ],
    style={
        "width": "100%",
        "margin": "0",
        "padding": "0",
    }
)

@app.callback(
    [Output('crash-map', 'figure'),
     Output('barchart', 'figure')],
    [Input('crash-map', 'hoverData'),
     Input('barchart', 'hoverData'),
     Input('barchart', 'clickData'),
     Input('crash-map', 'clickData'),
     ]
)
def update_map(hover_map, hover_bar, click_bar, click_data):

    bar = px.bar(state_count,
                 x='state_name',
                 y='crash_count',
                 title='States by Crash Count',
                 labels={'state_name': 'State', 'crash_count': 'Crashes'},
                 hover_data={'crash_count': True}
                 )

    bar.update_traces(
        hovertemplate="<b>%{x}</b><br>Crashes: %{y:,}<extra></extra>",
        hoverlabel=dict(
            bgcolor="lightblue",
            bordercolor="blue",
            font=dict(
                size=14,
                color="navy",
                family="Helvetica"
            )
        )
    )

    fig = px.choropleth_mapbox(
        state_count,  # Use the state_count DataFrame
        geojson=us_states,
        locations='state_name',
        featureidkey="properties.name",
        color='crash_count',  # Map crash_count to color
        color_continuous_scale="Blues",  # Choose a color scale that represents intensity
        hover_name='state_name',  # Display state name on hover
        hover_data={'crash_count': True},  # Include crash_count in hover
        center={'lat': 39.8282, 'lon': -98.5795},
        zoom=3,
        height=700,
        opacity=0,  # Adjust opacity
    )

    fig.update_traces(
        marker_line_color="black",
        marker_line_width=1,
        hovertemplate="<b>%{hovertext}</b><br>Crashes: %{customdata[0]}<extra></extra>",
        hoverlabel=dict(
            bgcolor="rgba(255, 255, 255, 0.8)",  # Semi-transparent white
            bordercolor="gray",
            font=dict(
                size=14,
                color="black",
                family="Helvetica"
            )
        )
    )

    fig.update_layout(
        mapbox_style="carto-darkmatter",
        font=dict(color='white', size=12),
        paper_bgcolor='darkgrey',
        showlegend=False
    )

    if hover_map or hover_bar:
        if hover_bar:
            hovered_state = hover_bar['points'][0]['label']

        if hover_map:
            hovered_state = hover_map['points'][0]['location']
        # Extract the geometry of the hovered state
        hovered_geometry = None
        for feature in us_states['features']:
            if feature['properties']['name'] == hovered_state:
                hovered_geometry = feature['geometry']
                break

        # If geometry is found, highlight it
        if hovered_geometry:
            lats, lons = [], []
            if hovered_geometry['type'] == 'Polygon':
                for coords in hovered_geometry['coordinates']:
                    lats.extend([point[1] for point in coords])
                    lons.extend([point[0] for point in coords])
            elif hovered_geometry['type'] == 'MultiPolygon':
                for polygon in hovered_geometry['coordinates']:
                    for coords in polygon:
                        lats.extend([point[1] for point in coords])
                        lons.extend([point[0] for point in coords])

            fig.add_trace(
                go.Scattermapbox(
                    lat=lats,
                    lon=lons,
                    mode='lines',
                    line=dict(
                        width=1,
                        color='lightgrey',

                    ),
                    opacity=0.2,
                    hoverinfo='skip',
                    name='Highlight_Hover'
                )
            )
        fig.update_mapboxes(uirevision=True)

    if click_data or click_bar:
        if click_bar:
            selected_state = click_bar['points'][0]['label']

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

        selected_geometry = None
        for feature in us_states['features']:
            if feature['properties']['name'] == selected_state:
                selected_geometry = feature['geometry']
                break

        if selected_geometry and selected_geometry['type'] == 'Polygon':
            for coords in selected_geometry['coordinates']:
                fig.add_trace(
                    go.Scattermapbox(
                        lon=[point[0] for point in coords],
                        lat=[point[1] for point in coords],
                        mode='lines',
                        line=dict(color='lightgrey', width=1),
                        hoverinfo='skip',
                        opacity=0.2
                    )
                )
        elif selected_geometry and selected_geometry['type'] == 'MultiPolygon':
            for polygon in selected_geometry['coordinates']:
                for coords in polygon:
                    fig.add_trace(
                        go.Scattermapbox(
                            lon=[point[0] for point in coords],
                            lat=[point[1] for point in coords],
                            mode='lines',
                            line=dict(color='lightgrey', width=1),
                            hoverinfo='skip',
                            opacity=0.2
                        )
                    )

        fig.update_mapboxes(
            zoom=5,
            center={
                'lat': states_center.loc[states_center['Name'] ==
                                         selected_state, 'Latitude'].values[0],
                'lon': states_center.loc[states_center['Name'] ==
                                         selected_state, 'Longitude'].values[0]
            },
        )

    return fig, bar


if __name__ == '__main__':
    app.run_server(debug=True)

