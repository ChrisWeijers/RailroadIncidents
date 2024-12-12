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
            Output('manual-zoom', 'data'),
            Output('selected-state', 'data'),
            Output('popup-title', 'children'),
            Output('popup-details', 'children'),
            Output('barchart', 'style'),
            Output('state-popup', 'style'),
            Output('barchart-button', 'style'),
            Output('clear-selection-button', 'style')
        ],
        [
            Input('crash-map', 'relayoutData'),
            Input('crash-map', 'clickData'),
            Input('barchart', 'clickData'),
            Input('sidebar-button', 'n_clicks'),
            Input('barchart-button', 'n_clicks'),
            Input('clear-selection-button', 'n_clicks')
        ],
        [
            State('manual-zoom', 'data'),
            State('selected-state', 'data')
        ]
    )
    def handle_interactions(relayout_data: Dict[str, Any], map_click: Dict[str, Any], bar_click: Dict[str, Any],
                           button_clicks: int, bar_button_clicks: int, clear_button_clicks: int,
                           current_zoom_state: Dict[str, Any], current_selected: str) -> tuple:
        """
        Handles interactions with the map, bar chart, and buttons.

        Updates the map zoom, selected state, popup content, and sidebar visibility.

        Args:
            relayout_data (dict): Data from map relayout event.
            map_click (dict): Data from map click event.
            bar_click (dict): Data from bar chart click event.
            button_clicks (int): Number of clicks on the sidebar button.
            bar_button_clicks (int): Number of clicks on the bar chart button.
            clear_button_clicks (int): Number of clicks on the clear button.
            current_zoom_state (dict): Current zoom and center of the map.
            current_selected (str): The currently selected state.

        Returns:
            tuple: A tuple containing updated zoom data, selected state, popup title, popup details,
                   barchart style, sidebar style, bar button style, and clear button style.
        """
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

        if trigger_id == 'sidebar-button' and button_clicks:
            barchart_style = {'display': 'block'}
            sidebar_style = {'display': 'none'}
            bar_button_style = {'display': 'block'}
        elif trigger_id == 'barchart-button' and bar_button_clicks:
            barchart_style = {'display': 'none'}
            sidebar_style = {'display': 'block'}
            bar_button_style = {'display': 'none'}
        else:
            sidebar_style = {'display': 'block' if current_selected else 'none'}
            barchart_style = {'display': 'none' if current_selected else 'block'}
            bar_button_style = {'display': 'none' if current_selected else 'block'}

        # Hide clear button if no state is selected
        clear_button_style = {'display': 'block' if current_selected else 'none'}

        if trigger_id == 'clear-selection-button':
            return (current_zoom_state, None, '', '', {'display': 'block'},
                    {'display': 'none'}, {'display': 'block'}, {'display': 'none'})

        return (current_zoom_state, current_selected, popup_title, popup_details, barchart_style,
                sidebar_style, bar_button_style, clear_button_style)

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
    def update_map(hover_map: Dict[str, Any], hover_bar: Dict[str, Any], selected_state: str,
                   relayout: Dict[str, Any], manual_zoom: Dict[str, Any],
                   year_range: List[int], month_range: List[int], damage_range: List[float],
                   injuries_range: List[int], speed_range: List[float]) -> tuple:
        """
        Updates the crash map and bar chart based on user interactions and filters.

        Filters data based on selected state, year, month, damage, injuries, and speed ranges.

        Args:
            hover_map (dict): Data from map hover event.
            hover_bar (dict): Data from bar chart hover event.
            selected_state (str): The currently selected state.
            relayout (dict): Data from map relayout event.
            manual_zoom (dict): Current zoom and center of the map.
            year_range (list): List containing min and max year for filtering.
            month_range (list): List containing min and max month for filtering.
            damage_range (list): List containing min and max damage for filtering.
            injuries_range (list): List containing min and max injuries for filtering.
            speed_range (list): List containing min and max speed for filtering.

        Returns:
            tuple: A tuple containing the updated map figure and bar chart figure.
        """
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