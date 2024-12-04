from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
from app.data import get_data
from app.plots import Map, BarChart

df, states_center, state_count, us_states = get_data()

app = Dash(__name__)
app.title = 'Railroad Dashboard'

app.layout = html.Div(
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
                  className='graph-container')
    ],
    style={
        "width": "100%",
        "margin": "0",
        "padding": "0",
    }
)


@app.callback(
    [Output('manual-zoom', 'data'),
     Output('selected-state', 'data')],
    [Input('crash-map', 'relayoutData'),
     Input('crash-map', 'clickData'),
     Input('barchart', 'clickData')],
    [State('manual-zoom', 'data'),
     State('selected-state', 'data')]
)
def handle_map_interactions(relayout_data, map_click, bar_click, current_zoom_state, current_selected):
    ctx = callback_context
    if not ctx.triggered:
        return current_zoom_state, current_selected

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trigger_prop = ctx.triggered[0]['prop_id'].split('.')[1]

    default_view = {
        'zoom': 3,
        'center': {'lat': 39.8282, 'lon': -98.5795}
    }

    # Handle map view changes
    if trigger_id == 'crash-map' and trigger_prop == 'relayoutData' and relayout_data:
        if all(key in relayout_data for key in ['mapbox.zoom', 'mapbox.center.lat', 'mapbox.center.lon']):
            return default_view, None

        if 'mapbox.zoom' in relayout_data or 'mapbox.center' in relayout_data:
            new_zoom = relayout_data.get('mapbox.zoom', current_zoom_state['zoom'])
            new_center = {
                'lat': relayout_data.get('mapbox.center', current_zoom_state['center'])['lat']
                if 'mapbox.center' in relayout_data else current_zoom_state['center']['lat'],
                'lon': relayout_data.get('mapbox.center', current_zoom_state['center'])['lon']
                if 'mapbox.center' in relayout_data else current_zoom_state['center']['lon']
            }
            return {'zoom': new_zoom, 'center': new_center}, current_selected

    # Handle clicks
    clicked_state = None
    if trigger_id == 'crash-map' and map_click:
        point_data = map_click['points'][0]
        clicked_state = point_data.get('customdata') or \
                        (point_data.get('text', '').split('<br>')[0] if point_data.get('text') else None)
    elif trigger_id == 'barchart' and bar_click:
        clicked_state = bar_click['points'][0].get('label') or bar_click['points'][0].get('x')

    if clicked_state:
        if clicked_state == current_selected:
            return default_view, None
        else:
            state_center = states_center.loc[states_center['Name'] == clicked_state]
            if not state_center.empty:
                return {
                    'zoom': 5,
                    'center': {
                        'lat': state_center.iloc[0]['Latitude'],
                        'lon': state_center.iloc[0]['Longitude']
                    }
                }, clicked_state

    return current_zoom_state, current_selected


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
    bar = BarChart(state_count).create_barchart()

    us = Map(df, us_states, state_count, manual_zoom)
    fig = us.plot_map()

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
                us.highlight_state(hovered_state, 'hoverstate')
        except Exception as e:
            print(f"Error processing hover data: {e}")

    # Handle selected state and points display
    if selected_state:
        df_state = df[df['state_name'] == selected_state]
        us.add_points(df_state, 'clickstate')

    if 'mapbox.zoom' in relayout:
        if relayout['mapbox.zoom'] >= 5:
            selected_state = None
            us.add_points(df, 'all_points')

    return fig, bar


if __name__ == '__main__':
    app.run_server(debug=False, dev_tools_ui=False)
