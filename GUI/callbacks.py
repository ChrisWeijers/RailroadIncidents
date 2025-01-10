import dash
from dash import Output, Input, State, callback
from dash import callback_context
from GUI.plots import Map, BarChart
from dash import html
import pandas as pd
from typing import List, Dict, Any

# Define compatible visualizations for each attribute type
COMPATIBLE_VIZ = {
    "Categorical": ["grouped_bar", "choropleth", "treemap"],
    "Ordered Quantitative": [
        "scatter",
        "scatter_size",
        "scatter_trendline",
        "boxplot",
    ],
    "Ordered Sequential": [
        "stacked_bar",
        "side_by_side_bar",
        "clustered_bar",
    ],
    "Ordered Cyclic": ["polar", "line"],
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

    This function defines callbacks for handling user interactions with the map,
    bar chart, sidebar, and various controls, which update the UI.

    Args:
        app (dash.Dash): The Dash application instance.
        df (pd.DataFrame): The main DataFrame containing the accident data.
        state_count (pd.DataFrame): DataFrame with crash counts per state.
        us_states (Dict[str, Any]): A dictionary of US states data.
    """

    @app.callback(
        [Output('manual-zoom', 'data')],
        [Input('crash-map', 'relayoutData')],
        [State('manual-zoom', 'data')]
    )
    def handle_layout_changes(relayout_data: Dict[str, Any], current_zoom_state: Dict[str, Any]):
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        if trigger_id == 'crash-map' and relayout_data:
            new_zoom = relayout_data.get('mapbox.zoom', current_zoom_state.get('zoom', 3))
            new_center = {
                'lat': relayout_data.get('mapbox.center', {}).get('lat', current_zoom_state.get('center', {}).get('lat', 37.8)),
                'lon': relayout_data.get('mapbox.center', {}).get('lon', current_zoom_state.get('center', {}).get('lon', -96))
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
        [Output('crash-map', 'figure'),
         Output('barchart', 'figure')],
        [Input('states-select', 'value'),
         Input('hovered-state', 'data'),
         Input('manual-zoom', 'data'),
         Input('range-slider', 'value')],  # Added slider input
    )
    def update_map(selected_state, hovered_state, manual_zoom, selected_range):
        """
        Updates the map and bar chart with filtered data based on slider range, state selection, and hover.
        """
        # Filter data based on slider range if the year column exists
        if 'corrected_year' in df.columns:
            df_filtered = df[(df['corrected_year'] >= selected_range[0]) &
                             (df['corrected_year'] <= selected_range[1])]
        else:
            df_filtered = df.copy()

        # Create initial figures
        bar = BarChart(state_count).create_barchart()
        us_map = Map(df_filtered, us_states, state_count, manual_zoom)
        fig_map = us_map.plot_map()

        # Highlight hovered state
        if hovered_state:
            us_map.highlight_state(hovered_state, 'hoverstate')

        # Add points and update bar chart for selected states
        if selected_state:
            if 'all' in selected_state:
                us_map.add_points(df_filtered, 'clickstate')
                bar = BarChart(state_count).create_barchart()
            else:
                us_map.highlight_state(selected_state, 'clickstate')

                if not isinstance(selected_state, list):
                    selected_state = [selected_state]
                state_data = df_filtered[df_filtered['state_name'].isin(selected_state)]
                us_map.add_points(state_data, 'clickstate')

                if len(selected_state) > 1:
                    state_count_filtered = state_count[state_count['state_name'].isin(selected_state)]
                    bar = BarChart(state_count_filtered).create_barchart()

        return fig_map, bar

    @app.callback(
        [
            Output('plot-left', 'figure'),
            Output('plot-right', 'figure'),
            Output('plot-left', 'style'),
            Output('plot-right', 'style'),
            Output('compare-attributes-dropdown', 'options'),
            Output('viz-dropdown', 'options'),
            Output('viz-dropdown', 'value'),
        ],
        [
            Input('attributes-dropdown', 'value'),
            Input('compare-attributes-dropdown', 'value'),
            Input('viz-dropdown', 'value'),
            Input('range-slider', 'value')  # Add range slider as an input
        ]
    )
    def update_charts_and_dropdowns(selected_attr, compare_attr, selected_viz, selected_range):
        """
        Updates charts and dropdown options dynamically based on selected attributes, visualizations, and date range.
        """
        print("Selected Range:", selected_range)
        fig_left, fig_right = {}, {}
        display_left, display_right = {"display": "none"}, {"display": "none"}

        if not selected_attr:
            print("No attribute selected.")
            return fig_left, fig_right, display_left, display_right, [], [], None

        # Filter data based on slider range
        df_filtered = df[(df['corrected_year'] >= selected_range[0]) & (df['corrected_year'] <= selected_range[1])]

        # Check if selected attributes exist in the DataFrame
        if selected_attr not in df_filtered.columns or (compare_attr and compare_attr not in df_filtered.columns):
            print("Selected attributes not found in DataFrame.")
            return fig_left, fig_right, display_left, display_right, [], [], None

        # Determine the selected attribute type
        attr_type = ATTRIBUTE_TYPES.get(selected_attr, None)
        if not attr_type:
            print("Attribute type not found.")
            return fig_left, fig_right, display_left, display_right, [], [], None

        # Populate compatible compare options and visualization options
        compare_options = [
            {"label": aliases.get(attr, attr), "value": attr}
            for attr, attr_type_2 in ATTRIBUTE_TYPES.items()
            if attr_type_2 in COMPATIBLE_TYPES.get(attr_type, []) and attr != selected_attr
        ]
        viz_options = [
            {"label": viz.replace("_", " ").capitalize(), "value": viz}
            for viz in COMPATIBLE_VIZ.get(attr_type, [])
        ]

        # Reset visualization dropdown if the selected visualization is not compatible
        if selected_viz not in [opt["value"] for opt in viz_options]:
            selected_viz = None

        # Generate figures if the selected visualization is compatible
        if selected_viz:
            if selected_viz == "scatter" and compare_attr:
                fig_left = px.scatter(
                    df_filtered,
                    x=selected_attr,
                    y=compare_attr,
                    title=f"Scatter: {aliases.get(selected_attr, selected_attr)} vs. {aliases.get(compare_attr, compare_attr)}",
                )
                display_left = {"display": "block"}

            elif selected_viz == "grouped_bar":
                grouped = df_filtered.groupby(selected_attr, as_index=False).mean()
                fig_left = px.bar(
                    grouped,
                    x=selected_attr,
                    y=compare_attr,
                    title=f"Grouped Bar Chart: Avg {aliases.get(compare_attr, compare_attr)} by {aliases.get(selected_attr, selected_attr)}",
                )
                display_left = {"display": "block"}

        return fig_left, fig_right, display_left, display_right, compare_options, viz_options, selected_viz
