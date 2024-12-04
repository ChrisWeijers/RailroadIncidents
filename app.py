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

# Handle any states missing from state_count
missing_states = pd.DataFrame({'state_name': states_center[~states_center['Name'].isin(state_count['state_name'])]['Name'],
                               'crash_count': 0})
state_count = pd.concat([state_count, missing_states], ignore_index=True)

# Initialize the app
app = Dash(__name__)
app.title = 'Railroad Dashboard'

# App layout
app.layout = html.Div(
    className='main-container',
    children=[
        # Sidebar Popup
        html.Div(
            id="popup-sidebar",
            className="popup-sidebar",
            children=[
                html.Div(
                    id="state-popup",
                    className="popup-content",
                    children=[
                        html.H3(id="popup-title"),
                        html.Div(id="popup-details"),
                        html.Button("Close", id="close-popup"),
                    ],
                )
            ],
            style={'display': 'none'}  # Initially hidden
        ),
        # Main content area
        html.Div(
            className='content-area',
            children=[
                dcc.Store(id='selected-state', storage_type='memory'),
                dcc.Store(id='manual-zoom', storage_type='memory',
                          data={'zoom': 3, 'center': {'lat': 39.8282, 'lon': -98.5795}}),

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
                dcc.Graph(id='barchart',
                          className='graph-container'),
            ]
        )
    ]
)

# Callback to handle map interactions and sidebar popup
@app.callback(
    [
        Output('popup-sidebar', 'style'),
        Output('manual-zoom', 'data'),
        Output('selected-state', 'data'),
        Output('popup-title', 'children'),
        Output('popup-details', 'children')
    ],
    [
        Input('crash-map', 'relayoutData'),
        Input('crash-map', 'clickData'),
        Input('barchart', 'clickData'),
        Input('close-popup', 'n_clicks')
    ],
    [
        State('manual-zoom', 'data'),
        State('selected-state', 'data')
    ]
)
def handle_map_interactions(relayout_data, map_click, bar_click, close_click, current_zoom_state, current_selected):
    ctx = callback_context
    if not ctx.triggered:
        return {'display': 'none'}, current_zoom_state, current_selected, "", ""

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trigger_prop = ctx.triggered[0]['prop_id'].split('.')[1]

    default_view = {
        'zoom': 3,
        'center': {'lat': 39.8282, 'lon': -98.5795}
    }

    # Handle closing the popup
    if trigger_id == 'close-popup' and close_click:
        return {'display': 'none'}, current_zoom_state, None, "", ""

    # Handle map view changes
    if trigger_id == 'crash-map' and trigger_prop == 'relayoutData' and relayout_data:
        if all(key in relayout_data for key in ['mapbox.zoom', 'mapbox.center.lat', 'mapbox.center.lon']):
            return {'display': 'none'}, default_view, None, "", ""

        if 'mapbox.zoom' in relayout_data or 'mapbox.center' in relayout_data:
            new_zoom = relayout_data.get('mapbox.zoom', current_zoom_state['zoom'])
            new_center = {
                'lat': relayout_data.get('mapbox.center', current_zoom_state['center'])['lat']
                if 'mapbox.center' in relayout_data else current_zoom_state['center']['lat'],
                'lon': relayout_data.get('mapbox.center', current_zoom_state['center'])['lon']
                if 'mapbox.center' in relayout_data else current_zoom_state['center']['lon']
            }
            return {'display': 'none'}, {'zoom': new_zoom, 'center': new_center}, current_selected, "", ""

    # Handle clicks
    clicked_state = None
    if trigger_id == 'crash-map' and map_click:
        point_data = map_click['points'][0]
        clicked_state = point_data.get('customdata') or \
                        (point_data.get('text', '').split('<br>')[0] if point_data.get('text') else None)
    elif trigger_id == 'barchart' and bar_click:
        clicked_state = bar_click['points'][0].get('label') or bar_click['points'][0].get('x')

    if clicked_state:
        state_center = states_center.loc[states_center['Name'] == clicked_state]
        if not state_center.empty:
            # Prepare content for the popup
            crash_count = state_count[state_count['state_name'] == clicked_state]['crash_count'].values[0]
            popup_title = f"{clicked_state}"
            popup_details = html.Div([
                html.P(f"Total Crashes: {crash_count}"),
                # Add more details here if needed
            ])
            return {'display': 'block'}, {
                'zoom': 5,
                'center': {
                    'lat': state_center.iloc[0]['Latitude'],
                    'lon': state_center.iloc[0]['Longitude']
                }
            }, clicked_state, popup_title, popup_details

    return {'display': 'none'}, current_zoom_state, current_selected, "", ""

# Main callback to update map and bar chart
@app.callback(
    [Output('crash-map', 'figure'),
     Output('barchart', 'figure')],
    [Input('crash-map', 'hoverData'),
     Input('barchart', 'hoverData'),
     Input('selected-state', 'data'),
     Input('crash-map', 'relayoutData'),
     Input('manual-zoom', 'data')]
)
def update_map(hover_map, hover_bar, selected_state, relayout, manual_zoom):
    # Create bar chart
    bar = px.bar(state_count,
                 x='state_name',
                 y='crash_count',
                 title='States by Crash Count',
                 labels={'state_name': 'State', 'crash_count': 'Crashes'},
                 hover_data={'crash_count': True})

    bar.update_traces(
        hovertemplate="<b>%{x}</b><br>Crashes: %{y:,}<extra></extra>",
        hoverlabel=dict(
            bgcolor="lightblue",
            bordercolor="blue",
            font=dict(size=14, color="navy", family="Helvetica")
        )
    )

    # Initialize the figure
    fig = go.Figure()

    # Add a single Choropleth layer for all states with transparent fill
    fig.add_trace(
        go.Choroplethmapbox(
            geojson=us_states,
            locations=state_count['state_name'],
            z=state_count['crash_count'],
            featureidkey="properties.name",
            colorscale=[[0, 'darkgrey'], [1, 'darkgrey']],
            marker_opacity=0.1,
            marker_line_width=0.5,
            marker_line_color='lightgrey',
            hoverinfo='text',
            customdata=state_count['state_name'],
            text=[f"{state}<br>Crashes: {count:,}" for state, count in zip(state_count['state_name'], state_count['crash_count'])],
            hovertemplate="<b>%{text}</b><extra></extra>",
            showscale=False,
            name='States'
        )
    )

    # Use manual_zoom for map center and zoom
    center = manual_zoom['center'] if manual_zoom else {'lat': 39.8282, 'lon': -98.5795}
    zoom = manual_zoom['zoom'] if manual_zoom else 3

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=center,
            zoom=zoom
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=900,
        paper_bgcolor='darkgrey',
        font=dict(color='white', size=12),
        showlegend=False,
        transition={'duration': 500, 'easing': 'elastic-in-out'}
    )

    # Handle hover interactions
    if hover_map or hover_bar:
        try:
            if hover_map:
                hovered_point = hover_map['points'][0]
                hovered_state = (hovered_point.get('customdata') or
                                 hovered_point.get('text', '').split('<br>')[0])
            else:
                hovered_point = hover_bar['points'][0]
                hovered_state = hovered_point.get('label') or hovered_point.get('name')

            if hovered_state:
                logging.debug(f"Hovered State: {hovered_state}")
                highlight_state(fig, hovered_state, 'hoverstate')
        except Exception as e:
            logging.error(f"Error processing hover data: {e}")

    # Handle selected state and points display
    if selected_state:
        df_state = df[df['state_name'] == selected_state]
        add_points(fig, df_state, selected_state, 'clickstate')

    if relayout and 'mapbox.zoom' in relayout:
        if relayout['mapbox.zoom'] >= 5:
            add_points(fig, df, None, 'all_points')

    return fig, bar

def add_points(fig, df_state, selected_state, name):
    """
    Adds incident points to the map for the selected state.
    """
    if df_state is not None and not df_state.empty:
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
                customdata=df_state['state_name'].tolist(),
                name=name,
            ),
        )

def highlight_state(fig, hovered_state, trace_name):
    """
    Adds a highlight trace for a hovered state to the figure.
    """
    hovered_geometry = None
    for feature in us_states['features']:
        if feature['properties']['name'] == hovered_state:
            hovered_geometry = feature['geometry']
            break

    if hovered_geometry and hovered_geometry['type'] == 'Polygon':
        for coords in hovered_geometry['coordinates']:
            fig.add_trace(
                go.Scattermapbox(
                    lon=[point[0] for point in coords],
                    lat=[point[1] for point in coords],
                    mode='lines',
                    line=dict(color='lightgrey', width=1),
                    hoverinfo='skip',
                    opacity=0.6,
                    name=trace_name,
                )
            )
    elif hovered_geometry and hovered_geometry['type'] == 'MultiPolygon':
        for polygon in hovered_geometry['coordinates']:
            for coords in polygon:
                fig.add_trace(
                    go.Scattermapbox(
                        lon=[point[0] for point in coords],
                        lat=[point[1] for point in coords],
                        mode='lines',
                        line=dict(color='lightgrey', width=1),
                        hoverinfo='skip',
                        opacity=0.6,
                        name=trace_name,
                    )
                )
    fig.update_layout(hovermode='closest', transition={'duration': 500, 'easing': 'elastic-in-out'})

if __name__ == '__main__':
    app.run_server(debug=True)
