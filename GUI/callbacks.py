from dash import Output, Input, State, callback_context
import pandas as pd
from typing import List, Dict, Any
from GUI.alias import incident_types, weather, visibility, cause_category_mapping, fra_cause_codes
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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
    HeatMap,
    StreamGraph,
    ParallelCategoriesPlot
)


def setup_callbacks(
        app,
        df: pd.DataFrame,
        state_count: pd.DataFrame,
        us_states: Dict[str, Any],
        df_map: pd.DataFrame,
        states_center,
        aliases: Dict[str, str],
        city_data: pd.DataFrame,
        crossing_data: pd.DataFrame,
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
            Input("show-cities", "value"),
            Input("show-crossings", "value")
        ],
    )
    def update_map(selected_states, hovered_state, manual_zoom, selected_range, show_cities, show_crossings):
        """
        Update the choropleth map and bar chart at the TOP
        based on state selection, hover, and date range.
        """
        df_filtered = filter_by_range(df, selected_range)

        us_map = Map(df_filtered, us_states, state_count, manual_zoom)
        fig_map = us_map.plot_map()

        # Basic horizontal bar chart
        bar = BarChart(df_filtered, states_center).create_barchart()

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
                bar = BarChart(filtered_states, states_center).create_barchart()

        # Add city data if the "show-cities" checkbox is checked
        if "show" in show_cities:
            fig_map.add_trace(
                px.scatter_mapbox(
                    city_data,
                    lat="lat",
                    lon="lng",
                    hover_name="city",
                    hover_data={"lat": False, "lng": False, "population": True},
                ).update_traces(
                    hovertemplate="<b>%{hovertext}</b><br>Population size: %{customdata}<extra></extra>",
                    customdata=city_data["population"],
                    marker=dict(size=10, color="cyan", symbol="circle", opacity=0.6),
                ).data[0]
            )

        # Add crossing data if the "show-crossings" checkbox is checked
        if "show" in show_crossings:
            fig_map.add_trace(
                px.scatter_mapbox(
                    crossing_data,
                    lat="Latitude",
                    lon="Longitude",
                    hover_name="Whistle Ban",  # Display "Whistle Ban" as the main label
                    hover_data={
                        "Latitude": False,  # Hide latitude
                        "Longitude": False,  # Hide longitude
                        "Track Signaled": True,  # Show if track is signaled
                        "Number Of Bells": True,  # Show the number of bells
                        "Traffic Lanes": True,  # Show the traffic lanes
                        "Crossing Illuminated": True,  # Show if the crossing is illuminated
                    },
                ).update_traces(
                    marker=dict(size=10, color="cyan", symbol="circle", opacity=0.6),
                    # Style consistent with city points
                    hovertemplate="<b>%{hovertext}</b><br>"
                                  "Track Signaled: %{customdata[0]}<br>"
                                  "Number Of Bells: %{customdata[1]}<br>"
                                  "Traffic Lanes: %{customdata[2]}<br>"
                                  "Crossing Illuminated: %{customdata[3]}<extra></extra>",
                    customdata=crossing_data[
                        ["Track Signaled", "Number Of Bells", "Traffic Lanes", "Crossing Illuminated"]
                    ].values,
                ).data[0]
            )

        return fig_map, bar

    @app.callback(
        [
            Output("plot-left", "figure"),
            Output("plot-left", "style"),
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
        fig_left = empty_fig
        style_left, style_right = hidden_style, {"color": "white", 'fontSize': 25}

        # Filter data by corrected_year range
        dff = filter_by_range(df.copy(), selected_range)

        # Filter by selected states (if any)
        if selected_states and "state_name" in dff.columns:
            dff = dff[dff["state_name"].isin(selected_states)]

        dff["TYPE"] = dff["TYPE"].astype(int, errors='ignore')
        dff["TYPE_LABEL"] = dff["TYPE"].map(incident_types)

        dff["WEATHER_LABEL"] = dff["WEATHER"].map(weather).fillna(dff["WEATHER"])
        dff["VISIBLTY_LABEL"] = dff["VISIBLTY"].map(visibility).fillna(dff["VISIBLTY"])
        dff["CAUSE_CATEGORY"] = dff["CAUSE"].map(cause_category_mapping).fillna("Unknown")
        if not selected_viz:
            return fig_left, style_left, style_right

        try:
            # ------------------ (1) Temporal Trends ------------------
            if selected_viz == "plot_1_1":
                # 1.1 Are total incidents increasing/decreasing over time?
                if "corrected_year" in dff.columns:
                    grouped = dff.groupby("DATE_M").size().reset_index(name="count_incidents")
                    fig_left = px.line(
                        grouped,
                        x="DATE_M",
                        y="count_incidents",
                        title="(1.1) Total Incidents Over Time",
                        labels={
                            "corrected_year": "Incident Year",
                            "count_incidents": "Incident Count",
                        },
                    )
                    fig_left.update_traces(mode="lines+markers", line=dict(width=3))
                    fig_left.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color="white"
                    )
                    style_left = display_style
                    style_right = hidden_style

            elif selected_viz == "plot_1_2":
                # 1.2 Which incident types show biggest changes over time?
                stream_graph = StreamGraph(aliases, dff, incident_types)
                fig_left = stream_graph.plot()

                fig_left.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color="white"
                )
                style_left = display_style
                style_right = hidden_style

            elif selected_viz == "plot_1_3":
                # 1.3 Seasonal patterns => use the HeatMap class
                heatmap_plotter = HeatMap(aliases=aliases,
                                          df=dff)

                bin_size = 1
                fig_left = heatmap_plotter.create(bin_size=bin_size, states=selected_states)
                fig_left.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color="white"
                )
                style_left = display_style
                style_right = hidden_style

            # ------------------ (2) Spatial Patterns ------------------
            elif selected_viz == "plot_2_1":
                if "state_name" in dff.columns and "TYPE_LABEL" in dff.columns:
                    top_states = (
                        dff["state_name"]
                        .value_counts()
                        .nlargest(10)
                        .reset_index()
                        .rename(columns={"index": "state_name", "state_name": "count"})
                    )

                    # Ensure columns are named correctly
                    top_states.columns = ["state_name", "count"]

                    # Filter data for these top states
                    dff_top_states = dff[dff["state_name"].isin(top_states["state_name"])]

                    # Prepare data for the sunburst chart
                    grouped = (
                        dff_top_states.groupby(["state_name", "TYPE_LABEL"])
                        .size()
                        .reset_index(name="count")
                    )

                    # Create a sunburst chart
                    fig_left = px.sunburst(
                        grouped,
                        path=["state_name", "TYPE_LABEL"],  # Hierarchical path
                        values="count",
                        title="(2.1) Top 10 States by Incident Count and Type",
                        color="count",
                        color_continuous_scale="Blues",
                    )
                    fig_left.update_traces(
                        hovertemplate="<b>%{label}</b><br>Count: %{value}",
                    )
                    # Update layout for better aesthetics
                    fig_left.update_layout(
                        margin=dict(t=30, l=0, r=0, b=0),
                        font=dict(size=14, color="white"),
                        paper_bgcolor="rgba(0,0,0,0)",
                    )

                    style_left = display_style
                    style_right = hidden_style


            elif selected_viz == "plot_2_3":
                # 2.3 Distribution differences => Parallel Categories Plot with selectable states
                if {"TYPE_LABEL", "ACCDMG", "WEATHER_LABEL", "TOTINJ", "TRNSPD", "state_name"}.issubset(dff.columns):
                    # Create bins for ACCDMG
                    bins_damage = [0, df["ACCDMG"].max() / 5, df["ACCDMG"].max() / 5 * 2, df["ACCDMG"].max() / 5 * 3,
                                   df["ACCDMG"].max() / 5 * 4, df["ACCDMG"].max()]
                    labels_damage = ["Low Damage", "Moderate Damage", "High Damage", "Severe Damage", "Extreme Damage"]
                    dff["ACCDMG_Binned"] = pd.cut(dff["ACCDMG"], bins=bins_damage, labels=labels_damage,
                                                  include_lowest=True)
                    # Create bins for Injuries
                    bins_injuries = [0, df["TOTINJ"].max() / 5, df["TOTINJ"].max() / 5 * 2, df["TOTINJ"].max() / 5 * 3,
                                     df["TOTINJ"].max() / 5 * 4, df["ACCDMG"].max()]
                    labels_injuries = ["No Injuries", "1-5 Injuries", "6-10 Injuries", "11-20 Injuries", "21+ Injuries"]
                    dff["Injuries_Binned"] = pd.cut(dff["TOTINJ"], bins=bins_injuries, labels=labels_injuries,
                                                    include_lowest=True)
                    # Create bins for Train Speed
                    bins_speed = [0, df["TRNSPD"].max() / 5, df["TRNSPD"].max() / 5 * 2, df["TRNSPD"].max() / 5 * 3,
                                  df["TRNSPD"].max() / 5 * 4, df["TRNSPD"].max()]
                    labels_speed = ["Very Slow", "Slow", "Moderate", "Fast", "Very Fast"]
                    dff["TRNSPD_Binned"] = pd.cut(dff["TRNSPD"], bins=bins_speed, labels=labels_speed,
                                                  include_lowest=True)
                    # Assign explicit colors dynamically based on selected states
                    dff["state_color"] = dff["state_name"].apply(
                        lambda x: "#FF0000" if x in selected_states else "#0000FF"  # Red for selected, Blue for others
                    )
                    # Filter and prepare data for PCP
                    selected_columns = ["TYPE_LABEL", "WEATHER_LABEL", "ACCDMG_Binned", "Injuries_Binned",
                                        "TRNSPD_Binned", "state_color"]
                    dff_filtered = dff[selected_columns]
                    # Create Parallel Categories Plot
                    fig_left = px.parallel_categories(
                        dff_filtered,
                        dimensions=["TYPE_LABEL", "WEATHER_LABEL", "ACCDMG_Binned", "Injuries_Binned", "TRNSPD_Binned"],
                        color="state_color",  # Use the explicit color column
                        labels={
                            "TYPE_LABEL": "Incident Type",
                            "ACCDMG_Binned": "Damage Category",
                            "WEATHER_LABEL": "Weather Condition",
                            "Injuries_Binned": "Injury Severity",
                            "TRNSPD_Binned": "Train Speed",
                            "state_color": "State Selection",
                        },
                        title="(2.3) Damage Distribution by Incident Type, Weather, and Injuries",
                    )
                    # Update layout for aesthetics
                    fig_left.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                    )

                    style_left = display_style
                    style_right = hidden_style

            elif selected_viz == "plot_3_2":
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
                    fig_left.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color="white"
                    )
                    style_left = display_style
                    style_right = hidden_style

            elif selected_viz == "plot_3_3":
                needed = ["CAUSE", "CARS", "TOTINJ"]

                if all(n in dff.columns for n in needed):
                    dff["CAUSE_CATEGORY"] = dff["CAUSE"].map(cause_category_mapping).fillna("Unknown")
                    grouped = dff.groupby("CAUSE_CATEGORY")[["CARS", "TOTINJ"]].sum().reset_index()
                    melted = grouped.melt(
                        id_vars=["CAUSE_CATEGORY"],
                        value_vars=["CARS", "TOTINJ"],
                        var_name="Factor",
                        value_name="Value",
                    )

                    fig_left = px.bar(
                        melted,
                        x="CAUSE_CATEGORY",
                        y="Value",
                        color="Factor",
                        barmode="stack",
                        title="(3.3) Factor Combos by Cause Category",
                        labels={
                            "CAUSE_CATEGORY": "Cause Category",
                            "Value": "Total Count",
                            "Factor": "Factor Type",
                        },
                    )
                    # Update layout for appearance
                    fig_left.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                    )
                    style_left = display_style
                    style_right = hidden_style

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
                    fig_left.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color="white"
                    )
                    style_left = display_style
                    style_right = hidden_style

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
                    fig_left.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color="white"
                    )
                    style_left = display_style
                    style_right = hidden_style

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
                    fig_left.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color="white"
                    )
                    style_left = display_style
                    style_right = hidden_style

            # ------------------ (5) High-Impact Incidents ------------------
            elif selected_viz == "plot_5_1":
                # 5.1 Primary & secondary causes => group by (CAUSE_CATEGORY, CAUSE2_CATEGORY)
                required_columns = ["CAUSE", "CAUSE2", "ACCDMG", "TOTINJ", "TOTKLD"]
                if all(col in dff.columns for col in required_columns):
                    # Define the outlier detection function
                    def is_outlier(series):
                        Q1 = series.quantile(0.25)
                        Q3 = series.quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        return (series < lower_bound) | (series > upper_bound)

                    # Apply outlier detection for each relevant column
                    outlier_damage = is_outlier(dff["ACCDMG"])
                    outlier_injuries = is_outlier(dff["TOTINJ"])
                    outlier_fatalities = is_outlier(dff["TOTKLD"])

                    # Combine outlier conditions
                    # Use logical OR (|) if you want to include incidents that are outliers in any one category
                    # Use logical AND (&) if you want to include only incidents that are outliers in all categories
                    outliers_condition = outlier_damage & outlier_injuries & outlier_fatalities  # Changed to OR

                    # Filter the DataFrame to include only outliers
                    dff_outliers = dff[outliers_condition].copy()

                    # Map both primary and secondary causes to their categories
                    dff_outliers["CAUSE_CATEGORY"] = dff_outliers["CAUSE"].map(cause_category_mapping).fillna("Unknown")
                    dff_outliers["CAUSE2_CATEGORY"] = dff_outliers["CAUSE2"].map(cause_category_mapping).fillna(
                        "Unknown")

                    # Group by cause categories and compute counts
                    grouped = dff_outliers.groupby(["CAUSE_CATEGORY", "CAUSE2_CATEGORY"]).size().reset_index(
                        name="count")

                    # Check if there are any outliers to plot
                    if not grouped.empty:
                        # Create the bar plot for outliers
                        fig_left = px.bar(
                            grouped,
                            x="CAUSE_CATEGORY",
                            y="count",
                            color="CAUSE2_CATEGORY",
                            barmode="group",
                            title="(5.1) Primary vs. Secondary Cause Categories (High-Impact Incidents)",
                            labels={
                                "CAUSE_CATEGORY": "Primary Cause Category",
                                "CAUSE2_CATEGORY": "Secondary Cause Category",
                                "count": "Number of High-Impact Incidents",
                            },
                        )

                        # Update the trace to adjust bar outline width
                        fig_left.update_traces(
                            marker=dict(
                                line=dict(
                                    width=0.3,  # Set the outline width here
                                )
                            )
                        )

                        # Calculate positions for vertical lines between primary cause categories
                        primary_categories = sorted(dff_outliers["CAUSE_CATEGORY"].unique())
                        number_of_primary = len(primary_categories)
                        line_positions = [i + 0.5 for i in range(1, number_of_primary)]

                        # Define vertical dotted lines
                        new_shapes = []
                        for pos in line_positions:
                            new_shapes.append(dict(
                                type='line',
                                x0=pos,
                                y0=0,
                                x1=pos,
                                y1=1,
                                xref='x',
                                yref='paper',
                                line=dict(
                                    color='white',  # Line color
                                    width=1,  # Line width
                                    dash='dot',  # Dash style
                                )
                            ))

                        # Handle existing shapes
                        existing_shapes = fig_left.layout.shapes or []  # Initialize as empty list if None

                        # Convert existing_shapes to a list if it's a tuple
                        if isinstance(existing_shapes, tuple):
                            existing_shapes = list(existing_shapes)
                        elif not isinstance(existing_shapes, list):
                            existing_shapes = []

                        # Concatenate existing shapes with new_shapes
                        combined_shapes = existing_shapes + new_shapes

                        # Update layout with combined shapes
                        fig_left.update_layout(
                            shapes=combined_shapes,
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="white",
                        )
                        style_left = display_style
                        style_right = hidden_style
                    else:
                        # If no outliers are found, create an empty figure with a message
                        fig_left = go.Figure()
                        fig_left.add_annotation(
                            x=0.5,
                            y=0.5,
                            text="No high-impact incidents detected based on the defined criteria.",
                            showarrow=False,
                            font=dict(color="white", size=14),
                            xref="paper",
                            yref="paper",
                            align="center",
                        )
                        fig_left.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="white",
                        )
                        style_left = display_style
                        style_right = hidden_style
                else:
                    # If required columns are missing, return an empty figure or a message
                    fig_left = go.Figure()
                    fig_left.add_annotation(
                        x=0.5,
                        y=0.5,
                        text="Required columns for high-impact incident analysis are missing.",
                        showarrow=False,
                        font=dict(color="white", size=14),
                        xref="paper",
                        yref="paper",
                        align="center",
                    )
                    fig_left.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                    )
                    style_left = display_style
                    style_right = hidden_style

            elif selected_viz == "plot_5_2":

                # Ensure necessary columns exist
                needed = ["ACCDMG", "TYPE_LABEL", "CAUSE"]
                if all(n in dff.columns for n in needed):
                    q1, q3 = dff["ACCDMG"].quantile([0.25, 0.75])
                    iqr = q3 - q1
                    outlier_threshold = q3 + 1.5 * iqr
                    # Filter to keep only outlier rows
                    outliers = dff[dff["ACCDMG"] > outlier_threshold]

                    if outliers.empty:
                        outliers = dff

                    outliers["CAUSE_CATEGORY"] = (
                        outliers["CAUSE"].map(cause_category_mapping).fillna("Unknown")
                    )

                    outliers["CAUSE_INFO"] = outliers["CAUSE"].map(
                        lambda x: next(
                            (desc
                             for cat in fra_cause_codes.values()
                             for subcat in cat.values()
                             if isinstance(subcat, dict)
                             for code, desc in subcat.items()
                             if code == x),
                            "Unknown cause"
                        )
                    )

                    grouped = (
                        outliers
                        .groupby(["TYPE_LABEL", "CAUSE_CATEGORY", "CAUSE", "CAUSE_INFO"])
                        .size()
                        .reset_index(name="count")
                    )

                    fig_left = px.sunburst(
                        grouped,
                        path=["TYPE_LABEL", "CAUSE_CATEGORY", "CAUSE"],  # Hierarchical path
                        values="count",
                        title="(5.2) Common Incident Types and Causes (Outliers by ACCDMG)",
                        color="count",
                        color_continuous_scale="Blues",
                    )

                    fig_left.update_traces(
                        hovertemplate=(
                            "<b>%{label}</b><br>"
                            "Count: %{value}<br>"
                            "Details: %{customdata}"
                            "<extra></extra>"
                        ),
                        customdata=grouped["CAUSE_INFO"],
                    )

                    fig_left.update_layout(
                        margin=dict(t=100, l=0, r=0, b=0),
                        font=dict(size=14, color="white"),
                        paper_bgcolor="rgba(0,0,0,0)",
                    )

                style_left = display_style
                style_right = hidden_style

            elif selected_viz == "plot_5_3":
                # 5.3 Preventable factors => grouped by ACCAUSE categories
                if "ACCAUSE" in dff.columns:
                    # Map ACCAUSE to its categories
                    dff["ACCAUSE_CATEGORY"] = dff["ACCAUSE"].map(cause_category_mapping).fillna("Unknown")
                    # Summarize data by ACCAUSE_CATEGORY
                    category_counts = dff["ACCAUSE_CATEGORY"].value_counts().reset_index()
                    category_counts.columns = ["Cause Category", "Count"]
                    # Create bar chart
                    fig_left = px.bar(
                        category_counts,
                        x="Cause Category",
                        y="Count",
                        title="(5.3) Preventable Factors in High-Impact Incidents (Grouped by Categories)",
                        labels={
                            "Cause Category": "Cause Category",
                            "Count": "Incident Count",
                        },
                    )
                    # Update layout for better appearance
                    fig_left.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                    )
                    style_left = display_style
                    style_right = hidden_style

            # ------------------ (6) Summarizing Incident Characteristics ------------------
            elif selected_viz == "plot_6_1":
                # 6.1 Most common types => TYPE_LABEL
                if "TYPE_LABEL" in dff.columns and "state_name" in dff.columns:
                    # Group data by TYPE_LABEL and state_name, then calculate counts
                    type_state_counts = (
                        dff.groupby(["TYPE_LABEL", "state_name"])
                        .size()
                        .reset_index(name="count")
                    )

                    # Filter to include only the top 10 most common incident types
                    top_types = type_state_counts.groupby("TYPE_LABEL")["count"].sum().nlargest(10).index
                    type_state_counts = type_state_counts[type_state_counts["TYPE_LABEL"].isin(top_types)]

                    # Create a stacked bar chart
                    fig_left = px.bar(
                        type_state_counts,
                        x="TYPE_LABEL",
                        y="count",
                        color="state_name",  # Use state_name to create the stacked effect
                        title="(6.1) Most Common Incident Types by State",
                        labels={
                            "TYPE_LABEL": "Incident Type",
                            "count": "Count",
                            "state_name": "State",
                        },
                    )
                    fig_left.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color="white"
                    )
                    style_left = display_style
                    style_right = hidden_style

            elif selected_viz == "plot_6_2":

                # 6.2 Most frequently cited primary causes => grouped by CAUSE categories
                if "CAUSE" in dff.columns:
                    # Map CAUSE to its categories
                    dff["CAUSE_CATEGORY"] = dff["CAUSE"].map(cause_category_mapping).fillna("Unknown")
                    category_counts = dff["CAUSE_CATEGORY"].value_counts().nlargest(10).reset_index()
                    category_counts.columns = ["Cause Category", "Count"]
                    fig_left = px.bar(
                        category_counts,
                        x="Cause Category",
                        y="Count",
                        title="(6.2) Most Frequent Primary Causes (Grouped by Categories)",
                        labels={
                            "Cause Category": "Cause Category",
                            "Count": "Incident Count",
                        },
                    )
                    fig_left.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color="white"
                    ),
                    style_left = display_style
                    style_right = hidden_style


            elif selected_viz == "plot_6_3":
                # 6.3 Avg damage cost among different incident types => violin plot x=TYPE_LABEL, y=ACCDMG without outliers
                if "TYPE_LABEL" in dff.columns and "ACCDMG" in dff.columns:
                    try:
                        # Calculate IQR for each TYPE_LABEL using groupby
                        q1 = dff.groupby("TYPE_LABEL")["ACCDMG"].transform(lambda x: x.quantile(0.25))
                        q3 = dff.groupby("TYPE_LABEL")["ACCDMG"].transform(lambda x: x.quantile(0.75))
                        iqr = q3 - q1
                        # Compute bounds for outliers
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        # Filter out the outliers
                        non_outliers = dff[dff["ACCDMG"].between(lower_bound, upper_bound)]
                        # Create violin plot without outliers=
                        fig_left = px.violin(
                            non_outliers,
                            x="TYPE_LABEL",
                            y="ACCDMG",
                            box=True,
                            points="all",  # Show only non-outlier points
                            title="(6.3) Damage Distribution by Incident Type (Without Outliers)",
                            labels={
                                "TYPE_LABEL": "Incident Type",
                                "ACCDMG": "Damage Cost",
                            },
                        )
                        # Update layout for better aesthetics and set fixed width
                        fig_left.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="white",
                            width=800,  # Set the fixed width of the plot
                            height=600,  # Set the fixed height of the plot
                            margin=dict(l=50, r=50, t=50, b=50),  # Adjust margins
                        )
                        style_left = display_style  # Show the plot
                        style_right = hidden_style
                    except Exception as e:
                        print(f"Error processing plot_6_3: {e}")
                        # Return an empty figure with an error message annotation
                        fig_left = go.Figure()
                        fig_left.add_annotation(
                            text="An error occurred while generating the plot.",
                            showarrow=False,
                            font=dict(size=16, color="white"),
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            align="center",
                        )
                        style_left = display_style  # Still display the error message
                        style_right = hidden_style
                    except Exception as e:
                        print(f"Error processing plot_6_3: {e}")
                        # Return an empty figure with an error message annotation
                        fig_left = go.Figure()
                        fig_left.add_annotation(
                            text="An error occurred while generating the plot.",
                            showarrow=False,
                            font=dict(size=16, color="white"),
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            align="center",
                        )
                        style_left = display_style  # Still display the error message
                        style_right = hidden_style

        except Exception as e:
            print(f"Error creating visualization '{selected_viz}': {e}")

        return fig_left, style_left, style_right
