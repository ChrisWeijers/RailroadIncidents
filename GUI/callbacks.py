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
        Output('states-select', 'value'),
        [Input('crash-map', 'clickData'),
         Input('barchart', 'clickData'),
         Input('states-select', 'value')],
        [State('selected-state', 'data')]
    )
    def handle_selection(map_click, bar_click, dropdown_selected, current_selected):
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        if not isinstance(dropdown_selected, list):
            dropdown_selected = [dropdown_selected]

        if trigger_id == 'crash-map' and map_click:
            point_data = map_click['points'][0]
            state = point_data.get('customdata') or point_data.get('text', '').split('<br>')[0]
            if state not in dropdown_selected:
                dropdown_selected.append(state)
        elif trigger_id == 'barchart' and bar_click:
            state = bar_click['points'][0].get('label') or bar_click['points'][0].get('x')
            if state not in dropdown_selected:
                dropdown_selected.append(state)

        return dropdown_selected

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

        if not selected_state:
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

    @app.callback(
        [Output('plot-left', 'figure'),
         Output('plot-right', 'figure'),
         Output('plot-left', 'style'),
         Output('plot-right', 'style')
         ],
        [
            Input('states-select', 'value'),
            Input('attributes-dropdown', 'value'),
            Input('viz-dropdown', 'value'),
            Input('plot-left', 'style'),
            Input('plot-right', 'style')
        ]
    )
    def update_bottom_charts(selected_states, selected_attrs, selected_viz, display_left, display_right):
        """
            Renders up to two charts in the bottom placeholders (plot-left, plot-right),
            based on user selections:
              - states-select (which states),
              - attributes-dropdown (which columns),
              - viz-dropdown (which chart types).
            """
        import plotly.express as px

        # 1) If user hasn't selected any visualization, return empty
        if not selected_viz:
            return {}, {}, {'display': 'none'}, {'display': 'none'}

        # 2) Filter by selected states (if 'all' not in the list)
        if selected_states and ('all' not in selected_states):
            dff = df[df['state_name'].isin(selected_states)]
        else:
            dff = df.copy()

        # 3) Decide how to handle multiple attributes
        #    If user picks 2, we can do x = first, y = second for scatter
        x_attr = selected_attrs[0] if selected_attrs else None
        y_attr = selected_attrs[1] if len(selected_attrs) > 1 else None

        # A small helper function to build a single figure
        def build_figure(vtype):
            if not vtype:
                return {}

            # SCATTER
            if vtype == 'scatter':
                if x_attr and y_attr:
                    fig = px.scatter(
                        dff,
                        x=x_attr,
                        y=y_attr,
                        color='state_name',
                        title=f"Scatter: {x_attr} vs. {y_attr}"
                    )
                else:
                    fig = {}
            # BAR
            elif vtype == 'bar':
                # If we have an x_attr, let's group by state and do average
                if x_attr:
                    grouped = dff.groupby('state_name', as_index=False)[x_attr].mean()
                    fig = px.bar(
                        grouped,
                        x='state_name',
                        y=x_attr,
                        title=f"Bar: avg({x_attr}) by State"
                    )
                else:
                    fig = {}
            # BOX
            elif vtype == 'box':
                if x_attr:
                    fig = px.box(
                        dff,
                        x='state_name',
                        y=x_attr,
                        title=f"Box Plot of {x_attr} by State"
                    )
                else:
                    fig = {}
            else:
                fig = {}

            return fig

        # 4) If user picked only one chart type, show it on the left
        #    If user picked 2 or more, show the first on the left, second on the right
        if len(selected_viz) == 1:
            left_fig = build_figure(selected_viz[0])
            right_fig = {}
            display_left = {'display': 'block'}
        else:
            left_fig = build_figure(selected_viz[0])
            right_fig = build_figure(selected_viz[1]) if len(selected_viz) > 1 else {}
            display_left = {'display': 'block'}
            display_right = {'display': 'block'}

        return left_fig, right_fig, display_left, display_right
