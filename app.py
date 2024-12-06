from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
from GUI.data import get_data
from GUI.plots import Map, BarChart

df, states_center, state_count, us_states = get_data()

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
        popup = {'display': 'none'}
        return popup, current_zoom_state, current_selected, "", ""

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trigger_prop = ctx.triggered[0]['prop_id'].split('.')[1]

    default_view = {
        'zoom': 3,
        'center': {'lat': 39.8282, 'lon': -98.5795}
    }

    # Handle closing the popup
    if trigger_id == 'close-popup' and close_click:
        popup = {'display': 'none'}
        return popup, default_view, None, "", ""

    # Handle map view changes (do NOT refresh the popup)
    if trigger_id == 'crash-map' and trigger_prop == 'relayoutData' and relayout_data:
        if 'mapbox.zoom' in relayout_data or 'mapbox.center' in relayout_data:
            new_zoom = relayout_data.get('mapbox.zoom', current_zoom_state['zoom'])
            new_center = {
                'lat': relayout_data.get('mapbox.center', current_zoom_state['center'])['lat']
                if 'mapbox.center' in relayout_data else current_zoom_state['center']['lat'],
                'lon': relayout_data.get('mapbox.center', current_zoom_state['center'])['lon']
                if 'mapbox.center' in relayout_data else current_zoom_state['center']['lon']
            }
            return {'display': 'block'}, {'zoom': new_zoom, 'center': new_center}, current_selected, "", ""

    # Handle clicks (only update popup when a state or bar chart is clicked)
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
            popup_details = html.Div([html.P(f"Total Crashes: {crash_count}")])
            popup = {'display': 'block'}
            return popup, current_zoom_state, clicked_state, popup_title, popup_details

    # If no specific interaction occurs, keep the current popup state
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
    bar = BarChart(state_count).create_barchart()

    us = Map(df, us_states, state_count, manual_zoom)
    fig = us.plot_map()

    # Handle hover interactions (optional highlighting)
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

    # Preserve selected state and popup on map movements
    if selected_state:
        df_state = df[df['state_name'] == selected_state]
        us.highlight_state(selected_state, 'clickstate')
        us.add_points(df_state, 'clickstate')

    # Add points when zoom level is sufficient
    if relayout and 'mapbox.zoom' in relayout:
        if relayout['mapbox.zoom'] >= 4.5:
            us.add_points(df, 'all_points')

    return fig, bar



if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_ui=False)
