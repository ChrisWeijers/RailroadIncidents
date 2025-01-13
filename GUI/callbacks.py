from dash import Output, Input, State
from GUI.plots import Map, ScatterPlot, BarChart, BoxPlot, GroupedBarChart, ClusteredBarChart
import pandas as pd
from typing import List, Dict, Any

ATTRIBUTE_TYPES = {
    "corrected_year": "Ordered Quantitative",
    "IMO": "Ordered Cyclic",
    "RAILROAD": "Categorical",
    "CARS": "Ordered Quantitative",
    "CARSDMG": "Ordered Quantitative",
    "CARSHZD": "Ordered Quantitative",
    "EVACUATE": "Ordered Quantitative",
    "TEMP": "Ordered Quantitative",
    "VISIBILITY": "Ordered Sequential",
    "WEATHER": "Categorical",
    "TRNSPD": "Ordered Quantitative",
    "TONS": "Ordered Quantitative",
    "LOADF1": "Ordered Quantitative",
    "LOADP1": "Ordered Quantitative",
    "EMPTYF1": "Ordered Quantitative",
    "EMPTYP1": "Ordered Quantitative",
    "LOADF2": "Ordered Quantitative",
    "LOADP2": "Ordered Quantitative",
    "EMPTYF2": "Ordered Quantitative",
    "EMPTYP2": "Ordered Quantitative",
    "ACCDMG": "Ordered Quantitative",
    "EQPDMG": "Ordered Quantitative",
    "TRKDMG": "Ordered Quantitative",
    "TOTINJ": "Ordered Quantitative",
    "TOTKLD": "Ordered Quantitative",
    "ENGRS": "Ordered Quantitative",
    "FIREMEN": "Ordered Quantitative",
    "CONDUCTR": "Ordered Quantitative",
    "BRAKEMEN": "Ordered Quantitative",
    "ALCOHOL": "Ordered Quantitative",
    "DRUG": "Ordered Quantitative",
}

# Define compatible visualizations for each attribute type
COMPATIBLE_VIZ = {
    "Categorical": ["grouped_bar"],
    "Ordered Quantitative": [
        "scatter",
        "scatter_size",
        "scatter_trendline",
        "boxplot",
    ],
    "Ordered Sequential": [
        "clustered_bar",
    ],
    "Ordered Cyclic": ["scatter_trendline"],
}

# Define compatible attribute types for comparisons
COMPATIBLE_TYPES = {
    "Categorical": ["Categorical", "Ordered Quantitative"],
    "Ordered Quantitative": ["Ordered Quantitative", "Categorical"],
    "Ordered Sequential": ["Ordered Sequential", "Ordered Quantitative"],
    "Ordered Cyclic": ["Ordered Cyclic", "Ordered Quantitative"],
}


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
                'lat': relayout_data.get('mapbox.center', {}).get('lat', current_zoom_state.get('center', {}).get('lat', 40.0)),
                'lon': relayout_data.get('mapbox.center', {}).get('lon', current_zoom_state.get('center', {}).get('lon', -100.0))
            }
            return {'zoom': new_zoom, 'center': new_center}
        return current_zoom_state

    @app.callback(
        Output('states-select', 'value'),
        [Input('crash-map', 'clickData'), Input('barchart', 'clickData')],
        [State('states-select', 'value')]
    )
    def handle_selection(map_click, bar_click, current_selected):
        """Update selected states based on user interaction with the map or bar chart."""
        selected_states = current_selected or []
        if map_click:
            state = map_click['points'][0].get('customdata') or map_click['points'][0].get('text', '').split('<br>')[0]
            if state and state not in selected_states:
                selected_states.append(state)
        elif bar_click:
            state = bar_click['points'][0].get('label') or bar_click['points'][0].get('x')
            if state and state not in selected_states:
                selected_states.append(state)
        return selected_states

    @app.callback(
        Output('hovered-state', 'data'),
        [Input('crash-map', 'hoverData'), Input('barchart', 'hoverData')]
    )
    def handle_hover(map_hover, bar_hover):
        """Highlight states when hovering over them in the map or bar chart."""
        if map_hover:
            return map_hover['points'][0].get('customdata') or map_hover['points'][0].get('text', '').split('<br>')[0]
        elif bar_hover:
            return bar_hover['points'][0].get('label') or bar_hover['points'][0].get('x')
        return None

    @app.callback(
        [
            Output('crash-map', 'figure'),
            Output('barchart', 'figure')
        ],
        [Input('states-select', 'value'), Input('hovered-state', 'data'), Input('manual-zoom', 'data'),
         Input('range-slider', 'value')]
    )
    def update_map(selected_states, hovered_state, manual_zoom, selected_range):
        """Update map and bar chart based on state selection, hover, and date range."""
        # Safely filter data using the updated filter_by_range function
        df_filtered = filter_by_range(df, selected_range)

        # **Debug: Print columns of df_filtered**
        print("df_filtered columns:", df_filtered.columns)

        try:
            us_map = Map(df_filtered, us_states, state_count, manual_zoom)
            fig_map = us_map.plot_map()
        except Exception as e:
            print(f"Error plotting map: {e}")
            fig_map = {}

        # Create Bar Chart using state_count
        try:
            # Ensure required columns exist
            if 'crash_count' not in state_count.columns or 'state_name' not in state_count.columns:
                raise ValueError("DataFrame must contain 'crash_count' and 'state_name' columns.")

            bar_chart_instance = BarChart(state_count)
            fig_barchart = bar_chart_instance.create_barchart()  # **No arguments passed**
        except Exception as e:
            print(f"Error creating bar chart: {e}")
            fig_barchart = {}  # Return an empty figure or a placeholder

        # Highlight hovered state
        if hovered_state:
            try:
                us_map.highlight_state(hovered_state, 'hoverstate')
            except Exception as e:
                print(f"Error highlighting state '{hovered_state}': {e}")

        # Update based on selected states
        if selected_states:
            if 'all' in selected_states:
                try:
                    us_map.add_points(df_filtered, 'clickstate')
                except Exception as e:
                    print(f"Error adding points for 'all' states: {e}")
            else:
                try:
                    us_map.highlight_state(selected_states, 'clickstate')
                except Exception as e:
                    print(f"Error highlighting selected states '{selected_states}': {e}")

                filtered_states = df_filtered[df_filtered['state_name'].isin(selected_states)]
                try:
                    us_map.add_points(filtered_states, 'clickstate')
                except Exception as e:
                    print(f"Error adding points for selected states '{selected_states}': {e}")

                filtered_state_count = state_count[state_count['state_name'].isin(selected_states)]
                try:
                    bar_chart_instance = BarChart(filtered_state_count)
                    fig_barchart = bar_chart_instance.create_barchart()  # **No arguments passed**
                except Exception as e:
                    print(f"Error creating filtered bar chart for states '{selected_states}': {e}")
                    fig_barchart = {}  # Return an empty figure or a placeholder

        return fig_map, fig_barchart

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
        compare_options = [
            {"label": aliases.get(attr, attr), "value": attr}
            for attr, type_ in ATTRIBUTE_TYPES.items()
            if type_ in COMPATIBLE_TYPES.get(attr_type, []) and attr != selected_attr
        ]

        # Initialize charts
        fig_left, fig_right = empty_fig, empty_fig
        display_left, display_right = hidden_style, hidden_style

        try:
            if selected_viz:
                if selected_viz == 'scatter':
                    scatter_instance = ScatterPlot(df_filtered)
                    fig_left = scatter_instance.create(
                        x_attr=selected_attr,
                        y_attr=compare_attr,
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                elif selected_viz == 'scatter_size':
                    scatter_size_instance = ScatterPlot(df_filtered)
                    fig_left = scatter_size_instance.create_with_size(
                        x_attr=selected_attr,
                        y_attr=compare_attr,
                        size_attr=compare_attr,  # Adjust based on logic
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                elif selected_viz == 'scatter_trendline':
                    scatter_trendline_instance = ScatterPlot(df_filtered)
                    fig_left = scatter_trendline_instance.create_with_trendline(
                        x_attr=selected_attr,
                        y_attr=compare_attr,
                        trendline='ols',
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                elif selected_viz == 'grouped_bar':
                    # Use GroupedBarChart with state_count
                    grouped_bar_instance = GroupedBarChart(state_count)
                    fig_left = grouped_bar_instance.create(
                        x_attr='state_name',
                        y_attr='crash_count',
                        group_attr='some_attribute',  # Replace with a valid grouping attribute
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                elif selected_viz == 'clustered_bar':
                    # Use ClusteredBarChart with state_count
                    clustered_bar_instance = ClusteredBarChart(state_count)
                    fig_left = clustered_bar_instance.create(
                        x_attr='state_name',
                        y_attr='crash_count',
                        cluster_attr='some_attribute',  # Replace with a valid clustering attribute
                        states=selected_states
                    )
                    display_left = {'display': 'block'}

                elif selected_viz == 'boxplot':
                    boxplot_instance = BoxPlot(df_filtered)
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