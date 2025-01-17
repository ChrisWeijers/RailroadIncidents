from dash import Output, Input, State, callback_context
import pandas as pd
from typing import List, Dict, Any
from GUI.alias import incident_types, weather, visibility
import plotly.express as px

# Import the plot classes you need:
from GUI.plots import (
    Map,
    ScatterPlot,
    BarChart,
    BoxPlot,
    GroupedBarChart,
    ClusteredBarChart,
    StackedBarChart,
    DomainPlots,
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
        # Filter by corrected_year
        if "corrected_year" in df_local.columns and selected_range and len(selected_range) == 2:
            start_yr, end_yr = selected_range
            mask = (df_local["corrected_year"] >= start_yr) & (df_local["corrected_year"] <= end_yr)
            return df_local[mask]
        return df_local

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
        hidden_style = {"display": "none"}
        display_style = {"display": "block"}

        empty_fig = {}
        fig_left, fig_right = empty_fig, empty_fig
        style_left, style_right = hidden_style, hidden_style

        # Filter data by corrected_year range
        dff = filter_by_range(df.copy(), selected_range)

        # Filter by selected states (if any)
        if selected_states and "state_name" in dff.columns:
            dff = dff[dff["state_name"].isin(selected_states)]

        # Map TYPE codes to labels
        if "TYPE" in dff.columns:
            dff["TYPE"] = dff["TYPE"].astype(str)
            dff["TYPE_LABEL"] = dff["TYPE"].map(incident_types).fillna("Unknown")

        dff["WEATHER_LABEL"] = dff["WEATHER"].map(weather).fillna(dff["WEATHER"])
        dff["VISIBLTY_LABEL"] = dff["VISIBLTY"].map(visibility).fillna(dff["VISIBLTY"])

        if not selected_viz:
            return fig_left, style_left, fig_right, style_right

        try:
            # ------------------ (1) Temporal Trends ------------------
            if selected_viz == "plot_1_1":
                # 1.1 Are total incidents increasing/decreasing over time?
                if "corrected_year" in dff.columns:
                    grouped = dff.groupby("corrected_year").size().reset_index(name="count_incidents")
                    fig_left = px.line(
                        grouped,
                        x="corrected_year",
                        y="count_incidents",
                        title="(1.1) Total Incidents Over Time",
                        labels={
                            "corrected_year": "Incident Year",
                            "count_incidents": "Incident Count",
                        },
                    )
                    fig_left.update_traces(mode="lines+markers", line=dict(width=3))
                    style_left = display_style

            elif selected_viz == "plot_1_2":
                # 1.2 Which incident types show biggest changes over time?
                # Use TYPE_LABEL with corrected_year
                if "corrected_year" in dff.columns and "TYPE_LABEL" in dff.columns:
                    grouped = (
                        dff.groupby(["corrected_year", "TYPE_LABEL"])
                        .size()
                        .reset_index(name="count_incidents")
                    )
                    fig_left = px.line(
                        grouped,
                        x="corrected_year",
                        y="count_incidents",
                        color="TYPE_LABEL",
                        title="(1.2) Incident Types Over Time",
                        labels={
                            "corrected_year": "Incident Year",
                            "TYPE_LABEL": "Incident Type",
                            "count_incidents": "Count",
                        },
                    )
                    style_left = display_style

            elif selected_viz == "plot_1_3":
                # 1.3 Seasonal patterns => group by 'IMO' (month)
                if "IMO" in dff.columns:
                    monthly = dff.groupby("IMO").size().reset_index(name="count_incidents")
                    fig_left = px.bar(
                        monthly,
                        x="IMO",
                        y="count_incidents",
                        title="(1.3) Seasonal Patterns by Month",
                        labels={
                            "IMO": "Incident Month",
                            "count_incidents": "Incident Count",
                        },
                    )
                    style_left = display_style

            # ------------------ (2) Spatial Patterns ------------------
            elif selected_viz == "plot_2_1":
                # 2.1 Highest geographic concentration => top 10 states
                if "state_name" in dff.columns:
                    top_states = dff["state_name"].value_counts().nlargest(10).reset_index()
                    top_states.columns = ["state_name", "count"]
                    fig_left = px.pie(
                        top_states,
                        names="state_name",
                        values="count",
                        title="(2.1) Top 10 States by Incident Count",
                    )
                    style_left = display_style

            elif selected_viz == "plot_2_2":
                # 2.2 Geographic factors => example box or bar
                # We do a bar: x=state_name, # of incidents
                if "state_name" in dff.columns:
                    st_counts = dff["state_name"].value_counts().reset_index()
                    st_counts.columns = ["state_name", "count"]
                    fig_left = px.bar(
                        st_counts,
                        x="state_name",
                        y="count",
                        title="(2.2) Incidents by State (Placeholder)",
                        labels={
                            "state_name": "State",
                            "count": "Count",
                        },
                    )
                    style_left = display_style

            elif selected_viz == "plot_2_3":
                # 2.3 Distribution differences => box x=TYPE_LABEL, y=ACCDMG
                if "TYPE_LABEL" in dff.columns and "ACCDMG" in dff.columns:
                    fig_left = px.box(
                        dff,
                        x="TYPE_LABEL",
                        y="ACCDMG",
                        title="(2.3) Damage Distribution by Incident Type",
                        labels={
                            "TYPE_LABEL": "Incident Type",
                            "ACCDMG": "Total Damage Cost",
                        },
                    )
                    style_left = display_style

            # ------------------ (3) Contributing Factors ------------------
            elif selected_viz == "plot_3_1":
                # 3.1 speed, weather, track => scatter x=TRNSPD, y=ACCDMG, color=WEATHER_LABEL
                needed = ["TRNSPD", "ACCDMG", "WEATHER_LABEL"]
                if all(col in dff.columns for col in needed):
                    fig_left = px.scatter(
                        dff,
                        x="TRNSPD",
                        y="ACCDMG",
                        color="WEATHER_LABEL",
                        title="(3.1) Speed vs. Damage (color=Weather)",
                        labels={
                            "TRNSPD": "Train Speed (mph)",
                            "ACCDMG": "Total Damage Cost",
                            "WEATHER_LABEL": "Weather Condition",
                        },
                    )
                    style_left = display_style

            elif selected_viz == "plot_3_2":
                # 3.2 How do factors affect severity => box x=WEATHER_LABEL, y=TOTINJ
                if "WEATHER_LABEL" in dff.columns and "TOTINJ" in dff.columns:
                    fig_left = px.box(
                        dff,
                        x="WEATHER_LABEL",
                        y="TOTINJ",
                        title="(3.2) Weather vs. Injuries",
                        labels={
                            "WEATHER_LABEL": "Weather Condition",
                            "TOTINJ": "Total Injuries",
                        },
                    )
                    style_left = display_style

            elif selected_viz == "plot_3_3":
                # 3.3 factor combos => stacked bar of CAUSE x [CARS, TOTINJ]
                needed = ["CAUSE", "CARS", "TOTINJ"]
                if all(n in dff.columns for n in needed):
                    melted = dff.melt(
                        id_vars=["CAUSE"],
                        value_vars=["CARS", "TOTINJ"],
                        var_name="Factor",
                        value_name="Value"
                    )
                    fig_left = px.bar(
                        melted,
                        x="CAUSE",
                        y="Value",
                        color="Factor",
                        barmode="stack",
                        title="(3.3) Factor Combos by Cause",
                    )
                    style_left = display_style

            # ------------------ (4) Operator Performance ------------------
            elif selected_viz == "plot_4_1":
                # 4.1 Compare overall incident rates across operators => RAILROAD
                if "RAILROAD" in dff.columns:
                    rr_counts = dff["RAILROAD"].value_counts().nlargest(10).reset_index()
                    rr_counts.columns = ["RAILROAD", "count"]
                    fig_left = px.bar(
                        rr_counts,
                        x="RAILROAD",
                        y="count",
                        title="(4.1) Top 10 Railroads by Incident Count",
                        labels={
                            "RAILROAD": "Reporting Railroad Code",
                            "count": "Count",
                        },
                    )
                    style_left = display_style

            elif selected_viz == "plot_4_2":
                # 4.2 Differences in incident types by operator => grouped bar
                if "RAILROAD" in dff.columns and "TYPE_LABEL" in dff.columns:
                    grouped = (
                        dff.groupby(["RAILROAD", "TYPE_LABEL"])
                        .size()
                        .reset_index(name="count")
                    )
                    fig_left = px.bar(
                        grouped,
                        x="RAILROAD",
                        y="count",
                        color="TYPE_LABEL",
                        barmode="group",
                        title="(4.2) Incident Types by Railroad",
                        labels={
                            "RAILROAD": "Reporting Railroad Code",
                            "TYPE_LABEL": "Incident Type",
                            "count": "Count",
                        },
                    )
                    style_left = display_style

            elif selected_viz == "plot_4_3":
                # 4.3 which operator is higher/lower => box x=RAILROAD, y=ACCDMG
                if "RAILROAD" in dff.columns and "ACCDMG" in dff.columns:
                    fig_left = px.box(
                        dff,
                        x="RAILROAD",
                        y="ACCDMG",
                        title="(4.3) Damage by Railroad",
                        labels={
                            "RAILROAD": "Reporting Railroad Code",
                            "ACCDMG": "Total Damage Cost",
                        },
                    )
                    style_left = display_style

            # ------------------ (5) High-Impact Incidents ------------------
            elif selected_viz == "plot_5_1":
                # 5.1 Primary & secondary causes => group by (CAUSE, CAUSE2)
                if "CAUSE" in dff.columns and "CAUSE2" in dff.columns:
                    grouped = dff.groupby(["CAUSE", "CAUSE2"]).size().reset_index(name="count")
                    fig_left = px.bar(
                        grouped,
                        x="CAUSE",
                        y="count",
                        color="CAUSE2",
                        barmode="group",
                        title="(5.1) Primary vs. Secondary Causes",
                    )
                    style_left = display_style

            elif selected_viz == "plot_5_2":
                # 5.2 Common circumstances in severe incidents => if ACCDMG>100000
                if "ACCDMG" in dff.columns and "TYPE_LABEL" in dff.columns:
                    severe = dff[dff["ACCDMG"] > 100000]
                    if severe.empty:
                        severe = dff
                    type_counts = severe["TYPE_LABEL"].value_counts().nlargest(5).reset_index()
                    type_counts.columns = ["TYPE_LABEL", "count"]
                    fig_left = px.pie(
                        type_counts,
                        names="TYPE_LABEL",
                        values="count",
                        title="(5.2) Common Incident Types in Severe Incidents",
                    )
                    style_left = display_style

            elif selected_viz == "plot_5_3":
                # 5.3 Preventable factors => e.g. ACCAUSE
                if "ACCAUSE" in dff.columns:
                    factor_counts = dff["ACCAUSE"].value_counts().nlargest(10).reset_index()
                    factor_counts.columns = ["ACCAUSE", "count"]
                    fig_left = px.bar(
                        factor_counts,
                        x="ACCAUSE",
                        y="count",
                        title="(5.3) Preventable Factors in High-Impact Incidents",
                    )
                    style_left = display_style

            # ------------------ (6) Summarizing Incident Characteristics ------------------
            elif selected_viz == "plot_6_1":
                # 6.1 Most common types => TYPE_LABEL
                if "TYPE_LABEL" in dff.columns:
                    type_counts = dff["TYPE_LABEL"].value_counts().nlargest(10).reset_index()
                    type_counts.columns = ["TYPE_LABEL", "count"]
                    fig_left = px.bar(
                        type_counts,
                        x="TYPE_LABEL",
                        y="count",
                        title="(6.1) Most Common Incident Types",
                        labels={
                            "TYPE_LABEL": "Incident Type",
                            "count": "Count",
                        },
                    )
                    style_left = display_style

            elif selected_viz == "plot_6_2":
                # 6.2 Most frequently cited primary causes => CAUSE
                if "CAUSE" in dff.columns:
                    cause_counts = dff["CAUSE"].value_counts().nlargest(10).reset_index()
                    cause_counts.columns = ["CAUSE", "count"]
                    fig_left = px.bar(
                        cause_counts,
                        x="CAUSE",
                        y="count",
                        title="(6.2) Most Frequent Primary Causes",
                    )
                    style_left = display_style

            elif selected_viz == "plot_6_3":
                # 6.3 Avg damage cost among different incident types => box x=TYPE_LABEL, y=ACCDMG
                if "TYPE_LABEL" in dff.columns and "ACCDMG" in dff.columns:
                    fig_left = px.box(
                        dff,
                        x="TYPE_LABEL",
                        y="ACCDMG",
                        title="(6.3) Avg Damage by Incident Type",
                        labels={
                            "TYPE_LABEL": "Incident Type",
                            "ACCDMG": "Damage Cost",
                        },
                    )
                    style_left = display_style

        except Exception as e:
            print(f"Error creating visualization '{selected_viz}': {e}")

        return fig_left, style_left, fig_right, style_right

