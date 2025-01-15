from dash import Output, Input, State, callback_context
import pandas as pd
from typing import List, Dict, Any

# Import the plot classes you need:
from GUI.plots import (
    Map,
    ScatterPlot,
    BarChart,
    BoxPlot,
    GroupedBarChart,
    ClusteredBarChart,
    StackedBarChart,
)

def setup_callbacks(
    app,
    df: pd.DataFrame,
    state_count: pd.DataFrame,
    us_states: Dict[str, Any],
    df_map: pd.DataFrame,
    aliases: Dict[str, str],
):
    """
    Sets up all the callback functions for the Dash application.
    """

    def filter_by_range(df_local, selected_range):
        """Helper function to filter data by the selected year range."""
        if selected_range and len(selected_range) == 2 and "corrected_year" in df_local.columns:
            return df_local[
                (df_local["corrected_year"] >= selected_range[0])
                & (df_local["corrected_year"] <= selected_range[1])
            ]
        return df_local.copy()

    # ------------------ Callbacks for TOP Map & Bar Chart ------------------ #
    @app.callback(
        Output("manual-zoom", "data"),
        [Input("crash-map", "relayoutData")],
        [State("manual-zoom", "data")],
    )
    def handle_layout_changes(relayout_data, current_zoom_state):
        """Updates the zoom and center of the map based on user interaction."""
        if relayout_data:
            new_zoom = relayout_data.get("mapbox.zoom", current_zoom_state.get("zoom", 3))
            new_center = {
                "lat": relayout_data.get("mapbox.center", {}).get(
                    "lat", current_zoom_state.get("center", {}).get("lat", 40.0)
                ),
                "lon": relayout_data.get("mapbox.center", {}).get(
                    "lon", current_zoom_state.get("center", {}).get("lon", -100.0)
                ),
            }
            return {"zoom": new_zoom, "center": new_center}
        return current_zoom_state

    @app.callback(
        Output("states-select", "value"),
        [Input("crash-map", "clickData"),
         Input("barchart", "clickData"),
         Input("states-select", "value")],
        [State("selected-state", "data")],
    )
    def handle_selection(map_click, bar_click, dropdown_selected, current_selected):
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        if not isinstance(dropdown_selected, list):
            dropdown_selected = [dropdown_selected]

        if trigger_id == "crash-map" and map_click:
            point_data = map_click["points"][0]
            st = point_data.get("customdata") or point_data.get("text", "").split("<br>")[0]
            if st and st not in dropdown_selected:
                dropdown_selected.append(st)
        elif trigger_id == "barchart" and bar_click:
            st = bar_click["points"][0].get("label") or bar_click["points"][0].get("x")
            if st and st not in dropdown_selected:
                dropdown_selected.append(st)

        return dropdown_selected

    @app.callback(
        Output("hovered-state", "data"),
        [Input("crash-map", "hoverData"), Input("barchart", "hoverData")],
    )
    def handle_hover(map_hover, bar_hover):
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        if trigger_id == "crash-map" and map_hover:
            pt = map_hover["points"][0]
            return pt.get("customdata") or pt.get("text", "").split("<br>")[0]
        elif trigger_id == "barchart" and bar_hover:
            return bar_hover["points"][0].get("label") or bar_hover["points"][0].get("x")
        return None

    @app.callback(
        [Output("crash-map", "figure"), Output("barchart", "figure")],
        [
            Input("states-select", "value"),
            Input("hovered-state", "data"),
            Input("manual-zoom", "data"),
            Input("range-slider", "value"),
        ],
    )
    def update_map(selected_states, hovered_state, manual_zoom, selected_range):
        """
        Update the choropleth map and bar chart at the TOP
        based on state selection, hover, and date range.
        """
        df_filtered = filter_by_range(df, selected_range)

        us_map = Map(df_filtered, us_states, state_count, manual_zoom)
        fig_map = us_map.plot_map()

        # Basic horizontal bar chart
        bar = BarChart(state_count).create_barchart()

        # Highlight hovered state
        if hovered_state:
            us_map.highlight_state(hovered_state, "hoverstate")

        # Add points for selected states if any
        if not selected_states:
            us_map.add_points(df_filtered, "clickstate")
        else:
            us_map.highlight_state(selected_states, "clickstate")

            filtered_states = df_filtered[df_filtered["state_name"].isin(selected_states)]
            us_map.add_points(filtered_states, "clickstate")

            if len(selected_states) > 1:
                filtered_state_count = state_count[state_count["state_name"].isin(selected_states)]
                bar = BarChart(filtered_state_count).create_barchart()

        return fig_map, bar

    # ------------------ Single Dropdown for 11 Visualizations ------------------ #
    @app.callback(
        [
            Output("plot-left", "figure"),
            Output("plot-left", "style"),
            Output("plot-right", "figure"),
            Output("plot-right", "style"),
        ],
        [
            Input("viz-dropdown", "value"),
            Input("range-slider", "value"),
            Input("states-select", "value"),
        ],
    )
    def update_bottom_visual(selected_viz, selected_range, selected_states):
        """
        Renders the bottom visualization(s) based on the selected_viz option.
        """
        hidden_style = {"display": "none"}
        display_style = {"display": "block"}

        empty_fig = {}
        fig_left, fig_right = empty_fig, empty_fig
        style_left, style_right = hidden_style, hidden_style

        # 1) Filter data by year range
        dff = filter_by_range(df, selected_range)
        # 2) Further filter by selected states
        if selected_states:
            dff = dff[dff["state_name"].isin(selected_states)]

        # If user hasn't picked any visualization
        if not selected_viz:
            return fig_left, style_left, fig_right, style_right

        # Prepare instances
        scatter_instance = ScatterPlot(aliases, dff)
        bar_instance = GroupedBarChart(aliases, dff)
        cluster_bar = ClusteredBarChart(aliases, dff)
        stacked_instance = StackedBarChart(aliases, dff)

        try:
            # (1) Compare total accidents & hazmat cars => "CARS" vs "CARSHZD"
            if selected_viz == "scatter_accidents_hazmat":
                fig_left = scatter_instance.create(
                    x_attr="CARS",    # Hazmat Cars Involved
                    y_attr="CARSHZD", # Hazmat Cars Released
                )
                style_left = display_style

            # (2) Compare hazmat cars damaged/derailed & released => "CARSDMG" vs "CARSHZD" w/ size
            elif selected_viz == "scatter_hazmat_damaged_vs_released":
                fig_left = scatter_instance.create_with_size(
                    x_attr="CARSDMG",
                    y_attr="CARSHZD",
                    size_attr="CARSHZD"
                )
                style_left = display_style

            # (3) Compare total accidents by state => x=state_name, y=CARS
            elif selected_viz == "compare_accidents_by_state":
                fig_left = bar_instance.create(
                    x_attr="state_name",
                    y_attr="CARS",
                )
                style_left = display_style

            # (4) Compare people injured/killed & hazmat cars => TOTINJ vs CARSDMG
            elif selected_viz == "scatter_injured_killed_hazmat":
                fig_left = scatter_instance.create(
                    x_attr="TOTINJ",   # total injuries
                    y_attr="CARSDMG", # hazmat cars damaged/derailed
                )
                style_left = display_style

            # (5) Compare total damage, equipment damage, track damage => stacked
            elif selected_viz == "stacked_damage_components":
                fig_left = stacked_instance.create(
                    category_col="state_name",
                    damage_cols=["ACCDMG", "EQPDMG", "TRKDMG"],
                )
                style_left = display_style

            # (6) Compare total damage & derailed loaded freight cars => ACCDMG vs LOADF2
            elif selected_viz == "scatter_damage_freight":
                fig_left = scatter_instance.create(
                    x_attr="ACCDMG",
                    y_attr="LOADF2",
                )
                style_left = display_style

            # (7) Compare accidents & positive/negative drug tests => x=DRUG, y=CARS
            elif selected_viz == "stacked_drug_tests":
                fig_left = cluster_bar.create(
                    x_attr="DRUG",
                    y_attr="CARS",
                )
                style_left = display_style

            # (8) Compare total accidents & train speed => x=TRNSPD, y=CARS
            elif selected_viz == "scatter_accidents_speed":
                fig_left = scatter_instance.create(
                    x_attr="TRNSPD",
                    y_attr="CARS",
                )
                style_left = display_style

            # (9) Compare people injured/killed & derailed loaded passenger cars => TOTINJ vs LOADP2
            elif selected_viz == "scatter_injured_passenger":
                fig_left = scatter_instance.create(
                    x_attr="TOTINJ",
                    y_attr="LOADP2",
                )
                style_left = display_style

            # (10) Compare brakemen on duty vs. derailed freight => x=BRAKEMEN, y=LOADF2
            elif selected_viz == "clustered_brakemen_freight":
                fig_left = cluster_bar.create(
                    x_attr="BRAKEMEN",
                    y_attr="LOADF2",
                )
                style_left = display_style

            # (11) Compare total damage & loaded passenger cars => x=ACCDMG, y=LOADP1
            elif selected_viz == "scatter_damage_passenger":
                fig_left = scatter_instance.create(
                    x_attr="ACCDMG",
                    y_attr="LOADP1",
                )
                style_left = display_style

            # If none matched
            else:
                pass

        except Exception as e:
            print(f"Error creating visualization '{selected_viz}': {e}")

        return fig_left, style_left, fig_right, style_right
