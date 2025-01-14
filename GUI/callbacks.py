from dash import Output, Input, State, callback_context
from GUI.plots import Map, ScatterPlot, BarChart, BoxPlot, GroupedBarChart, ClusteredBarChart
import pandas as pd
from typing import List, Dict, Any
from GUI.alias import (groups, ATTRIBUTE_TYPES, COMPATIBLE_TYPES, COMPATIBLE_VIZ,
                      create_grouped_options, create_comparison_options)

def setup_callbacks(app, df: pd.DataFrame, state_count: pd.DataFrame, us_states: Dict[str, Any],
                    df_map: pd.DataFrame, aliases: Dict[str, str]) -> None:
    """
    Sets up all the callback functions for the Dash application.

    Args:
        app (dash.Dash): The Dash application instance.
        df (pd.DataFrame): The main DataFrame containing the accident data.
        state_count (pd.DataFrame): DataFrame with crash counts per state.
        us_states (Dict[str, Any]): A dictionary of US states data.
        df_map (pd.DataFrame): DataFrame for the map plotting.
        aliases (Dict[str, str]): Dictionary mapping attribute names to their aliases.
    """

    def filter_by_range(df, selected_range):
        """Helper function to filter data by the selected range."""
        if selected_range and isinstance(selected_range, (list, tuple)) and len(selected_range) == 2:
            if 'corrected_year' in df.columns:
                return df[
                    (df['corrected_year'] >= selected_range[0]) &
                    (df['corrected_year'] <= selected_range[1])
                    ]
        return df.copy()

    @app.callback(
        Output('manual-zoom', 'data'),
        [Input('crash-map', 'relayoutData')],
        [State('manual-zoom', 'data')]
    )
    def handle_layout_changes(relayout_data, current_zoom_state):
        """Update the zoom and center of the map based on user interaction."""
        if relayout_data:
            new_zoom = relayout_data.get('mapbox.zoom', current_zoom_state.get('zoom', 3))
            new_center = {
                'lat': relayout_data.get('mapbox.center', {}).get('lat', current_zoom_state.get('center', {}).get('lat',
                                                                                                                  40.0)),
                'lon': relayout_data.get('mapbox.center', {}).get('lon', current_zoom_state.get('center', {}).get('lon',
                                                                                                                  -100.0))
            }
            return {'zoom': new_zoom, 'center': new_center}
        return current_zoom_state

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
            return point_data.get('customdata') or point_data.get('text', '').split('<br>')[0]
        elif trigger_id == 'barchart' and bar_hover:
            return bar_hover['points'][0].get('label') or bar_hover['points'][0].get('x')

        return None

    @app.callback(
        [
            Output('crash-map', 'figure'),
            Output('barchart', 'figure')
        ],
        [Input('states-select', 'value'),
         Input('hovered-state', 'data'),
         Input('manual-zoom', 'data'),
         Input('range-slider', 'value')]
    )
    def update_map(selected_states, hovered_state, manual_zoom, selected_range):
        """Update map and bar chart based on state selection, hover, and date range."""
        # Safely filter data using the updated filter_by_range function
        df_filtered = filter_by_range(df, selected_range)

        us_map = Map(df_filtered, us_states, state_count, manual_zoom)
        fig_map = us_map.plot_map()

        try:
            bar = BarChart(state_count).create_barchart()
        except:
            bar = BarChart(state_count).create_barchart()

        # Highlight hovered state
        if hovered_state:
            us_map.highlight_state(hovered_state, 'hoverstate')

        # Update based on selected states
        if not selected_states:
            us_map.add_points(df_filtered, 'clickstate')
        else:
            us_map.highlight_state(selected_states, 'clickstate')

            filtered_states = df_filtered[df_filtered['state_name'].isin(selected_states)]
            us_map.add_points(filtered_states, 'clickstate')

            if len(selected_states) > 1:
                filtered_state_count = state_count[state_count['state_name'].isin(selected_states)]
                bar = BarChart(filtered_state_count).create_barchart()

        return fig_map, bar

    @app.callback(
        [
            Output('plot-left', 'figure'),
            Output('plot-right', 'figure'),
            Output('plot-left', 'style'),
            Output('plot-right', 'style'),
            Output('compare-attributes-dropdown', 'options'),
            Output('viz-dropdown', 'options'),
            Output('viz-dropdown', 'value')
        ],
        [
            Input('attributes-dropdown', 'value'),
            Input('compare-attributes-dropdown', 'value'),
            Input('viz-dropdown', 'value'),
            Input('range-slider', 'value'),
            Input('states-select', 'value')
        ]
    )
    def update_charts_and_dropdowns(selected_attr, compare_attr, selected_viz, selected_range, selected_states):
        """Update dropdowns and visualizations dynamically based on user selections."""

        # Initialize empty figures and hide plot areas by default
        empty_fig = {}
        hidden_style = {'display': 'none'}

        # Define default outputs
        default_outputs = (
            empty_fig,  # plot-left.figure
            empty_fig,  # plot-right.figure
            hidden_style,  # plot-left.style
            hidden_style,  # plot-right.style
            [],  # compare-attributes-dropdown.options
            [],  # viz-dropdown.options
            None  # viz-dropdown.value
        )

        if not selected_attr:
            # No attribute selected; return defaults
            return default_outputs

        # Safely filter data using the updated filter_by_range function
        df_filtered = filter_by_range(df, selected_range)

        attr_type = ATTRIBUTE_TYPES.get(selected_attr)
        if not attr_type:
            # Attribute type not found; return defaults
            return default_outputs

        # Update compare options based on compatible types
        compare_options = create_comparison_options(df.columns, aliases, attr_type, selected_attr)

        # Initialize charts
        fig_left, fig_right = empty_fig, empty_fig
        display_left, display_right = hidden_style, hidden_style

        try:
            if selected_viz:
                if selected_viz == 'scatter':
                    scatter_instance = ScatterPlot(aliases, df_filtered)
                    fig_left = scatter_instance.create(
                        x_attr=selected_attr,
                        y_attr=compare_attr,
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                elif selected_viz == 'scatter_size':
                    scatter_size_instance = ScatterPlot(aliases, df_filtered)
                    fig_left = scatter_size_instance.create_with_size(
                        x_attr=selected_attr,
                        y_attr=compare_attr,
                        size_attr=compare_attr,  # Adjust based on logic
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                elif selected_viz == 'scatter_trendline':
                    scatter_trendline_instance = ScatterPlot(aliases, df_filtered)
                    fig_left = scatter_trendline_instance.create_with_trendline(
                        x_attr=selected_attr,
                        y_attr=compare_attr,
                        trendline='ols',
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                elif selected_viz == 'grouped_bar':
                    # Use GroupedBarChart with state_count
                    grouped_bar_instance = GroupedBarChart(aliases, state_count)
                    fig_left = grouped_bar_instance.create(
                        x_attr='state_name',
                        y_attr='crash_count',
                        group_attr='some_attribute',  # Replace with a valid grouping attribute
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                elif selected_viz == 'clustered_bar':
                    # Use ClusteredBarChart with state_count
                    clustered_bar_instance = ClusteredBarChart(aliases, state_count)
                    fig_left = clustered_bar_instance.create(
                        x_attr='state_name',
                        y_attr='crash_count',
                        cluster_attr='some_attribute',  # Replace with a valid clustering attribute
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                elif selected_viz == 'boxplot':
                    boxplot_instance = BoxPlot(aliases, df_filtered)
                    fig_left = boxplot_instance.create(
                        x_attr=selected_attr,
                        y_attr=compare_attr,
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                else:
                    # Unsupported visualization type
                    print(f"Unsupported visualization type selected: {selected_viz}")
                    return default_outputs

        except Exception as e:
            # Handle exceptions gracefully
            print(f"Error creating visualization '{selected_viz}': {e}")
            return default_outputs

        # Determine compatible visualizations based on the selected attribute type
        viz_options = COMPATIBLE_VIZ.get(attr_type, [])
        viz_options_formatted = [
            {"label": viz.replace('_', ' ').title(), "value": viz} for viz in viz_options
        ]

        return (
            fig_left,  # plot-left.figure
            fig_right,  # plot-right.figure
            display_left,  # plot-left.style
            display_right,  # plot-right.style
            compare_options,  # compare-attributes-dropdown.options
            viz_options_formatted,  # viz-dropdown.options
            selected_viz  # viz-dropdown.value
        )
