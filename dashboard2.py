from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import numpy as np
import json
import plotly.graph_objects as go
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load and preprocess data
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

# Select relevant columns
fips_codes = fips_codes[['fips', 'state_name']].copy()

# Correct year values
df['corrected_year'] = np.where(df['YEAR'] > 24.0, 1900 + df['YEAR'], 2000 + df['YEAR'])

# Clean data
df = df.dropna(subset=['Latitude', 'Longitud']).drop_duplicates(subset=['Latitude', 'Longitud'])

# Merge with FIPS codes to get state names
df = pd.merge(df, fips_codes, left_on='STATE', right_on='fips').drop('fips', axis=1)

# Ensure consistent state names by stripping whitespace and standardizing case
df['state_name'] = df['state_name'].str.strip().str.title()
states_center['Name'] = states_center['Name'].str.strip().str.title()

# Load GeoJSON for US states
with open('data/us-states.geojson', 'r') as geojson_file:
    us_states = json.load(geojson_file)

# Aggregate crash counts by state
state_count = df.groupby('state_name').size().reset_index(name='crash_count').sort_values(by='crash_count', ascending=False)
diff = pd.concat([states_center['Name'], state_count['state_name']]).drop_duplicates(keep=False).to_frame()
diff.columns = ['state_name']
diff.insert(1, 'crash_count', [0] * len(diff))
state_count = pd.concat([state_count, diff])

app = Dash(__name__, assets_folder='assets')

app.layout = html.Div(
    children=[
        # Hidden Stores
        dcc.Store(id='selected-state', storage_type='memory'),
        dcc.Store(id='manual-zoom', storage_type='memory', data={'zoom': 3, 'center': {'lat': 39.8282, 'lon': -98.5795}}),
        dcc.Store(id='show-popup', data=False),  # Store for popup visibility

        # Main Container with Flex Layout
        html.Div(
            className='main-container',
            children=[
                # Popup Sidebar
                html.Div(
                    id="popup-sidebar",
                    className="popup-sidebar",
                    children=[
                        html.Div(
                            id="popup-content",  # Container for dynamic content
                            className="popup-content",
                            children=[
                                html.H3("State Details"),
                                html.Div(id="popup-details"),
                                dcc.Slider(
                                    id="example-slider",
                                    min=0,
                                    max=100,
                                    step=1,
                                    value=50,
                                    marks={i: str(i) for i in range(0, 101, 20)},
                                ),
                                html.Button("Close", id="close-popup"),
                            ]
                        )
                    ]
                ),

                # Main Content Area
                html.Div(
                    className='content-area',
                    children=[
                        html.H1("Interactive Railroad Accidents by State", style={"textAlign": "center"}),
                        dcc.Graph(
                            id='crash-map',
                            className='graph-container',
                            config={
                                'scrollZoom': True,
                                'doubleClick': 'reset',
                                'displayModeBar': True,
                            },
                        ),
                        dcc.Graph(id='barchart', className='graph-container'),
                    ]
                ),
            ]
        )
    ]
)

@app.callback(
    [
        Output('crash-map', 'figure'),
        Output('barchart', 'figure'),
        Output('manual-zoom', 'data'),
        Output('selected-state', 'data'),
        Output('popup-sidebar', 'style'),
        Output('popup-details', 'children')  # Dynamically update popup details
    ],
    [
        Input('crash-map', 'clickData'),
        Input('barchart', 'clickData'),
        Input('close-popup', 'n_clicks'),
    ],
    [
        State('manual-zoom', 'data'),
        State('selected-state', 'data')
    ]
)
def update_map(map_click, bar_click, close_click, manual_zoom, selected_state):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Default values
    zoom_data = manual_zoom or {'zoom': 3, 'center': {'lat': 39.8282, 'lon': -98.5795}}
    state_selected = selected_state
    popup_style = {'display': 'none'}  # Hide sidebar by default
    popup_details = ""

    # Handle map or bar chart clicks
    if trigger_id == 'crash-map' and map_click:
        state_selected = map_click['points'][0].get('customdata') or map_click['points'][0].get('text', '').split('<br>')[0]
        logging.debug(f"Clicked State: {state_selected}")
        popup_style = {'display': 'block'}  # Show sidebar

        # Populate the popup with state details
        state_data = df[df['state_name'] == state_selected]
        total_crashes = state_data.shape[0]
        year_min = state_data['corrected_year'].min()
        year_max = state_data['corrected_year'].max()
        unique_locations = state_data[['Latitude', 'Longitud']].drop_duplicates().shape[0]

        popup_details = html.Div(
            children=[
                html.P(f"State: {state_selected}", style={"fontWeight": "bold", "color": "#ffffff"}),
                html.P(f"Total Crashes: {total_crashes}", style={"color": "#ffffff"}),
                html.P(f"Year Range: {year_min} - {year_max}", style={"color": "#ffffff"}),
                html.P(f"Unique Crash Locations: {unique_locations}", style={"color": "#ffffff"}),
            ]
        )

    elif trigger_id == 'barchart' and bar_click:
        state_selected = bar_click['points'][0]['x']
        logging.debug(f"Bar Chart Selected State: {state_selected}")
        popup_style = {'display': 'block'}  # Show sidebar

        # Populate the popup with state details
        state_data = df[df['state_name'] == state_selected]
        total_crashes = state_data.shape[0]
        year_min = state_data['corrected_year'].min()
        year_max = state_data['corrected_year'].max()
        unique_locations = state_data[['Latitude', 'Longitud']].drop_duplicates().shape[0]

        popup_details = html.Div(
            children=[
                html.P(f"State: {state_selected}", style={"fontWeight": "bold", "color": "#ffffff"}),
                html.P(f"Total Crashes: {total_crashes}", style={"color": "#ffffff"}),
                html.P(f"Year Range: {year_min} - {year_max}", style={"color": "#ffffff"}),
                html.P(f"Unique Crash Locations: {unique_locations}", style={"color": "#ffffff"}),
            ]
        )

    elif trigger_id == 'close-popup' and close_click:
        state_selected = None
        popup_style = {'display': 'none'}  # Hide sidebar
        popup_details = ""

    # Update zoom to state
    if state_selected:
        state_center = states_center[states_center['Name'] == state_selected]
        if not state_center.empty:
            lat, lon = state_center.iloc[0]['Latitude'], state_center.iloc[0]['Longitude']
            zoom_data = {'zoom': 5, 'center': {'lat': lat, 'lon': lon}}

    # Create bar chart
    bar = px.bar(
        state_count,
        x='state_name',
        y='crash_count',
        title='States by Crash Count',
        labels={'state_name': 'State', 'crash_count': 'Crashes'}
    )

    # Create map figure
    fig = go.Figure()

    # Add Choropleth layer
    fig.add_trace(
        go.Choroplethmapbox(
            geojson=us_states,
            locations=state_count['state_name'],
            z=state_count['crash_count'],
            featureidkey="properties.name",
            colorscale=[[0, 'lightgrey'], [1, 'darkred']],
            marker_opacity=0.6,
            marker_line_width=0.5,
            hoverinfo='text',
            text=[f"{state}<br>Crashes: {count:,}" for state, count in
                  zip(state_count['state_name'], state_count['crash_count'])],
            hovertemplate="<b>%{text}</b><extra></extra>",
            showscale=False,
        )
    )

    # Add points for selected state
    if state_selected:
        state_data = df[df['state_name'] == state_selected]
        fig.add_trace(
            go.Scattermapbox(
                lat=state_data['Latitude'],
                lon=state_data['Longitud'],
                mode='markers',
                marker=dict(size=6, color='darkred', opacity=0.7),
                text=state_data['state_name'],
                hoverinfo='text',
                name=state_selected,
            )
        )

    # Update map layout
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=zoom_data['center'],
            zoom=zoom_data['zoom']
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=900
    )

    return fig, bar, zoom_data, state_selected, popup_style, popup_details

if __name__ == '__main__':
    app.run_server(debug=True)
