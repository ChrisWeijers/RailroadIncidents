import dash
from dash import Output, Input, State, callback
from dash import callback_context
from GUI.plots import Map, BarChart
from dash import html
import pandas as pd
from typing import List, Dict, Any


def setup_callbacks(app, df: pd.DataFrame, state_count: pd.DataFrame, us_states: Dict[str, Any]) -> None:
    """
    Sets up all the callback functions for the Dash application.

    This function defines callbacks for handling user interactions with the map,
    bar chart, sidebar, and various controls, which update the UI.

    Args:
        app (dash.Dash): The Dash application instance.
        df (pd.DataFrame): The main DataFrame containing the accident data.
        state_count (pd.DataFrame): DataFrame with crash counts per state.
        us_states (Dict[str, Any]): A dictionary of US states data.
    """

    @app.callback(
        [
            Output('manual-zoom', 'data')
        ],
        [
            Input('crash-map', 'relayoutData')
        ],
        [
            State('manual-zoom', 'data')
        ]
    )
    def handle_layout_changes(relayout_data: Dict[str, Any], current_zoom_state: Dict[str, Any]):
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        if trigger_id == 'crash-map' and relayout_data:
            new_zoom = relayout_data.get('mapbox.zoom', current_zoom_state.get('zoom', 3))  # Default zoom level 3
            new_center = {
                'lat': relayout_data.get('mapbox.center', {}).get('lat', current_zoom_state.get('center', {}).get('lat',
                                                                                                                  37.8)),
                'lon': relayout_data.get('mapbox.center', {}).get('lon',
                                                                  current_zoom_state.get('center', {}).get('lon', -96))
            }
            current_zoom_state = {'zoom': new_zoom, 'center': new_center}

        return [current_zoom_state]

    @app.callback(
        [
            Output('states-select', 'value')
        ],
        [
            Input('crash-map', 'clickData'),
            Input('barchart', 'clickData'),
        ],
        [
            State('selected-state', 'data'),
        ]
    )
    def handle_selection(map_click, bar_click, current_selected):
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        selected_state = []
        if trigger_id == 'crash-map' and map_click:
            point_data = map_click['points'][0]
            selected_state = [point_data.get('customdata') or point_data.get('text', '').split('<br>')[0]]
        elif trigger_id == 'barchart' and bar_click:
            selected_state = [bar_click['points'][0].get('label') or bar_click['points'][0].get('x')]

        # If a state is clicked while 'all' is selected, deselect 'all'
        if selected_state and current_selected and 'all' in current_selected:
            current_selected.remove('all')

        return selected_state

    @app.callback(
        Output('hovered-state', 'data'),
        [
            Input('crash-map', 'hoverData'),
            Input('barchart', 'hoverData'),
        ]
    )
    def handle_hover(map_hover, bar_hover):
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        hovered_state = str()
        if trigger_id == 'crash-map' and map_hover:
            point_data = map_hover['points'][0]
            hovered_state = point_data.get('customdata') or point_data.get('text', '').split('<br>')[0]
        elif trigger_id == 'barchart' and bar_hover:
            hovered_state = bar_hover['points'][0].get('label') or bar_hover['points'][0].get('x')

        return hovered_state

    @app.callback(
        [
            Output('crash-map', 'figure'),
            Output('barchart', 'figure')
        ],
        [
            Input('states-select', 'value'),
            Input('hovered-state', 'data'),
            Input('manual-zoom', 'data'),
        ]
    )
    def update_map(selected_state, hovered_state, manual_zoom):
        bar = BarChart(state_count).create_barchart()
        us = Map(df, us_states, state_count, manual_zoom)
        fig = us.plot_map()

        if hovered_state:
            us.highlight_state(hovered_state, 'hoverstate')

        if selected_state:
            # Check if 'all' is in the selection
            if 'all' in selected_state:
                # Show all data points
                us.add_points(df, 'clickstate')
                # Show full bar chart
                bar = BarChart(state_count).create_barchart()
            else:
                us.highlight_state(selected_state, 'clickstate')

                if type(selected_state) is not list:
                    selected_state = [selected_state]
                df_filtered = df[
                    (df['state_name'].isin(selected_state))
                ]
                us.add_points(df_filtered, 'clickstate')
                if len(selected_state) > 1:
                    state_count_filtered = state_count[
                        state_count['state_name'].isin(selected_state)
                    ]
                    bar = BarChart(state_count_filtered).create_barchart()

        return fig, bar
