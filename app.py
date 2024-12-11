from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
from GUI.data import get_data
from GUI.plots import Map, BarChart

df, states_center, state_count, us_states = get_data()

# Ensure these columns exist and are numeric. Adjust if needed.
year_min = int(df['corrected_year'].min())
year_max = int(df['corrected_year'].max())

month_min = int(df['IMO'].min())
month_max = int(df['IMO'].max())

damage_min = df['ACCDMG'].min()
damage_max = 3500000

injuries_min = df['TOTINJ'].min()
injuries_max = 400

speed_min = df['TRNSPD'].min()
speed_max = df['TRNSPD'].max()

app = Dash(__name__)
app.title = 'Railroad Dashboard'

app.layout = html.Div(
    className='main-container',
    children=[
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

                        # Year Range Slider
                        html.Label("Select Year Range"),
                        dcc.RangeSlider(
                            id='year-slider',
                            min=year_min,
                            max=year_max,
                            value=[year_min, year_max],
                            marks={str(y): str(y) for y in range(year_min, year_max+1, 2)},
                            step=1
                        ),

                        # Month Slider
                        html.Label("Select Month"),
                        dcc.RangeSlider(
                            id='month-slider',
                            min=month_min,
                            max=month_max,
                            value=[month_min, month_max],
                            marks={str(m): str(m) for m in range(month_min, month_max+1)},
                            step=1
                        ),

                        # Damage Slider
                        html.Label("Select Damage Range"),
                        dcc.RangeSlider(
                            id='damage-slider',
                            min=damage_min,
                            max=damage_max,
                            value=[damage_min, damage_max],
                            marks={
                                str(int(d)): str(int(d)) for d in [
                                    damage_min,
                                    (damage_min+damage_max)//2,
                                    damage_max
                                ]
                            },
                            step=(damage_max - damage_min)/100.0 if damage_max > damage_min else 1
                        ),

                        # Injuries Slider
                        html.Label("Select Injuries Range"),
                        dcc.RangeSlider(
                            id='injuries-slider',
                            min=injuries_min,
                            max=injuries_max,
                            value=[injuries_min, injuries_max],
                            marks={
                                str(int(i)): str(int(i)) for i in [
                                    injuries_min,
                                    (injuries_min+injuries_max)//2,
                                    injuries_max
                                ]
                            },
                            step=1
                        ),

                        # Speed Slider
                        html.Label("Select Speed Range"),
                        dcc.RangeSlider(
                            id='speed-slider',
                            min=speed_min,
                            max=speed_max,
                            value=[speed_min, speed_max],
                            marks={
                                str(int(s)): str(int(s)) for s in [
                                    speed_min,
                                    (speed_min+speed_max)//2,
                                    speed_max
                                ]
                            },
                            step=1
                        ),
                    ],
                )
            ]
        ),

        html.Div(
            className='content-area',
            children=[
                dcc.Store(id='selected-state', storage_type='memory'),
                dcc.Store(
                    id='manual-zoom',
                    storage_type='memory',
                    data={'zoom': 3, 'center': {'lat': 40.003, 'lon': -102.0517}}
                ),

                html.H1("Interactive Railroad Accidents by State", style={"textAlign": "center"}),

                dcc.Graph(
                    id='crash-map',
                    className='graph-container',
                    config={
                        'scrollZoom': True,
                        'doubleClick': 'reset',
                        'displayModeBar': True,
                    }
                ),

                dcc.Graph(
                    id='barchart',
                    className='graph-container'
                ),
            ]
        )
    ]
)

@app.callback(
    [
        Output('manual-zoom', 'data'),
        Output('selected-state', 'data'),
        Output('popup-title', 'children'),
        Output('popup-details', 'children')
    ],
    [
        Input('crash-map', 'relayoutData'),
        Input('crash-map', 'clickData'),
        Input('barchart', 'clickData'),
    ],
    [
        State('manual-zoom', 'data'),
        State('selected-state', 'data')
    ]
)
def handle_interactions(relayout_data, map_click, bar_click, current_zoom_state, current_selected):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    clicked_state = None
    if trigger_id == 'crash-map' and map_click:
        point_data = map_click['points'][0]
        clicked_state = point_data.get('customdata') or (
            point_data.get('text', '').split('<br>')[0] if point_data.get('text') else None
        )
    elif trigger_id == 'barchart' and bar_click:
        clicked_state = bar_click['points'][0].get('label') or bar_click['points'][0].get('x')

    if clicked_state:
        current_selected = clicked_state

    if trigger_id == 'crash-map' and relayout_data:
        new_zoom = relayout_data.get('mapbox.zoom', current_zoom_state['zoom'])
        new_center = {
            'lat': relayout_data.get('mapbox.center', current_zoom_state['center'])['lat']
            if 'mapbox.center' in relayout_data else current_zoom_state['center']['lat'],
            'lon': relayout_data.get('mapbox.center', current_zoom_state['center'])['lon']
            if 'mapbox.center' in relayout_data else current_zoom_state['center']['lon']
        }
        current_zoom_state = {'zoom': new_zoom, 'center': new_center}

    if current_selected:
        if current_selected in state_count['state_name'].values:
            crash_count = state_count[state_count['state_name'] == current_selected]['crash_count'].values[0]
            popup_title = current_selected
            popup_details = html.Div([html.P(f"Total Crashes: {crash_count}")])
        else:
            popup_title = current_selected
            popup_details = html.Div([html.P("No data available")])
    else:
        popup_title = ""
        popup_details = ""

    return current_zoom_state, current_selected, popup_title, popup_details

@app.callback(
    [Output('crash-map', 'figure'),
     Output('barchart', 'figure')],
    [
        Input('crash-map', 'hoverData'),
        Input('barchart', 'hoverData'),
        Input('selected-state', 'data'),
        Input('crash-map', 'relayoutData'),
        Input('manual-zoom', 'data'),
        Input('year-slider', 'value'),
        Input('month-slider', 'value'),
        Input('damage-slider', 'value'),
        Input('injuries-slider', 'value'),
        Input('speed-slider', 'value')
    ]
)
def update_map(hover_map, hover_bar, selected_state, relayout, manual_zoom,
               year_range, month_range, damage_range, injuries_range, speed_range):
    bar = BarChart(state_count).create_barchart()
    us = Map(df, us_states, state_count, manual_zoom)
    fig = us.plot_map()

    hovered_state = None
    if hover_map:
        hovered_point = hover_map['points'][0]
        hovered_state = hovered_point.get('customdata') or hovered_point.get('text', '').split('<br>')[0]
    elif hover_bar:
        hovered_point = hover_bar['points'][0]
        hovered_state = hovered_point.get('label') or hovered_point.get('name')

    if hovered_state:
        us.highlight_state(hovered_state, 'hoverstate')

    if selected_state:
        df_filtered = df[
            (df['state_name'] == selected_state) &
            (df['corrected_year'] >= year_range[0]) & (df['corrected_year'] <= year_range[1]) &
            (df['IMO'] >= month_range[0]) & (df['IMO'] <= month_range[1]) &
            (df['ACCDMG'] >= damage_range[0]) & (df['ACCDMG'] <= damage_range[1]) &
            (df['TOTINJ'] >= injuries_range[0]) & (df['TOTINJ'] <= injuries_range[1]) &
            (df['TRNSPD'] >= speed_range[0]) & (df['TRNSPD'] <= speed_range[1])
        ]

        us.highlight_state(selected_state, 'clickstate')
        us.add_points(df_filtered, 'clickstate')

    if relayout and 'mapbox.zoom' in relayout:
        if relayout['mapbox.zoom'] >= 4.5:
            df_all_filtered = df[
                (df['corrected_year'] >= year_range[0]) & (df['corrected_year'] <= year_range[1]) &
                (df['IMO'] >= month_range[0]) & (df['IMO'] <= month_range[1]) &
                (df['ACCDMG'] >= damage_range[0]) & (df['ACCDMG'] <= damage_range[1]) &
                (df['TOTINJ'] >= injuries_range[0]) & (df['TOTINJ'] <= injuries_range[1]) &
                (df['TRNSPD'] >= speed_range[0]) & (df['TRNSPD'] <= speed_range[1])
            ]
            us.add_points(df_all_filtered, 'all_points')

    return fig, bar

if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_ui=False)
