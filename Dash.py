import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import json
import us  # Install this library using "pip install us"

# Load railroad accident data
file_path = 'data/Railroad_Equipment_Accident_Incident.csv'
df = pd.read_csv(file_path, delimiter=',', low_memory=False)

# Preprocess data: ensure valid lat/lon and filter U.S. bounds
df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitud'] = pd.to_numeric(df['Longitud'], errors='coerce')
df = df[
    (df['Latitude'].between(24.396308, 49.384358)) &
    (df['Longitud'].between(-125.0, -66.93457))
]

# Load GeoJSON for U.S. states
with open('data/us-states.geojson', 'r') as geojson_file:
    us_states = json.load(geojson_file)

# Create a mapping of FIPS codes to state names
fips_to_state = {state.fips: state.name for state in us.states.STATES}

# Initialize Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Interactive Railroad Accidents by State", style={"textAlign": "center"}),

    # Map
    dcc.Graph(id='state-map', style={"height": "700px"}),

    # Filters for accidents
    html.Div([
        html.Label("Train Speed (mph):"),
        dcc.RangeSlider(
            id='speed-filter',
            min=0, max=150, step=5,
            marks={i: f"{i} mph" for i in range(0, 151, 25)},
            value=[0, 150]
        ),
        html.Label("Deaths:"),
        dcc.RangeSlider(
            id='deaths-filter',
            min=0, max=50, step=1,
            marks={i: f"{i}" for i in range(0, 51, 10)},
            value=[0, 50]
        ),
        html.Label("Injuries:"),
        dcc.RangeSlider(
            id='injuries-filter',
            min=0, max=500, step=10,
            marks={i: f"{i}" for i in range(0, 501, 100)},
            value=[0, 500]
        ),
        html.Label("Accident Damage ($):"),
        dcc.RangeSlider(
            id='damage-filter',
            min=0, max=1000000, step=50000,
            marks={i: f"${i:,}" for i in range(0, 1000001, 200000)},
            value=[0, 1000000]
        ),
    ], style={"padding": "20px", "backgroundColor": "#f9f9f9", "marginTop": "20px"}),
])

# Callbacks
@app.callback(
    Output('state-map', 'figure'),
    [
        Input('state-map', 'clickData'),
        Input('speed-filter', 'value'),
        Input('deaths-filter', 'value'),
        Input('injuries-filter', 'value'),
        Input('damage-filter', 'value')
    ]
)
def update_map(click_data, speed_range, deaths_range, injuries_range, damage_range):
    center_lat, center_lon = 37.8, -96.0
    zoom_level = 3

    # Default map showing state boundaries
    fig = px.choropleth_mapbox(
        geojson=us_states,
        locations=[state['properties']['name'] for state in us_states['features']],
        featureidkey="properties.name",
        color_discrete_sequence=["rgba(0,0,0,0)"],
        hover_name=[state['properties']['name'] for state in us_states['features']],
        center={"lat": center_lat, "lon": center_lon},
        zoom=zoom_level,
        height=700
    )
    fig.update_traces(marker_line_color="black", marker_line_width=1)

    if click_data:
        # Extract clicked state name
        selected_state = click_data['points'][0]['location']

        # Convert state name to FIPS code if needed
        state_fips = next((fips for fips, name in fips_to_state.items() if name == selected_state), None)

        # Filter dataset for selected state
        filtered_df = df[df['STATE'] == state_fips]

        # Apply slider filters
        filtered_df = filtered_df[
            (filtered_df['TRNSPD'] >= speed_range[0]) & (filtered_df['TRNSPD'] <= speed_range[1]) &
            (filtered_df['CASKLD'] >= deaths_range[0]) & (filtered_df['CASKLD'] <= deaths_range[1]) &
            (filtered_df['CASINJ'] >= injuries_range[0]) & (filtered_df['CASINJ'] <= injuries_range[1]) &
            (filtered_df['ACCDMG'] >= damage_range[0]) & (filtered_df['ACCDMG'] <= damage_range[1])
        ]

        # Add accident points to the map
        fig = px.scatter_mapbox(
            filtered_df,
            lat="Latitude",
            lon="Longitud",
            color="CASKLD",  # Color by deaths or another variable
            size="ACCDMG",  # Size by accident damage
            hover_data=["TRNSPD", "CASKLD", "CASINJ", "ACCDMG"],
            color_continuous_scale="Reds",
            zoom=5,
            height=700
        )

    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(center={"lat": center_lat, "lon": center_lon}, zoom=zoom_level)
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
