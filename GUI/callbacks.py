from dash import Output, Input, State, callback_context, dcc, html
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
    ParallelCategoriesPlot,
    WeatherHeatMap
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

        # Get current zoom level
        current_zoom = manual_zoom["zoom"]

        # Highlight hovered state
        if hovered_state:
            us_map.highlight_state(hovered_state, "hoverstate")

        # Add points for selected states if any
        if not selected_states:
            us_map.add_points(df_filtered, "clickstate")
            crossing_data_filtered = crossing_data
            city_data_filtered = city_data
        else:
            us_map.highlight_state(selected_states, "clickstate")

            filtered_states = df_filtered[df_filtered["state_name"].isin(selected_states)]
            us_map.add_points(filtered_states, "clickstate")

            if len(selected_states) > 1:
                bar = BarChart(filtered_states, states_center).create_barchart()

            # Filter city and crossing data based on selected states
            crossing_data_filtered = crossing_data[crossing_data["State Name"].isin(selected_states)]
            city_data_filtered = city_data[city_data["state_name"].isin(selected_states)]

        # Add city data if the "show-cities" checkbox is checked
        if "show" in show_cities:
            fig_map.add_trace(
                px.scatter_mapbox(
                    city_data_filtered,
                    lat="lat",
                    lon="lng",
                    hover_name="city",
                    hover_data={"lat": False, "lng": False, "population": True},
                ).update_traces(
                    hovertemplate="<b>%{hovertext}</b><br>Population size: %{customdata}<extra></extra>",
                    customdata=city_data_filtered["population"],
                    marker=dict(size=max(5, min(20, 5 + (current_zoom * 1.5)) - (40 / (current_zoom + 3))),
                                color="#FF00FF", symbol="circle", opacity=0.9),
                ).data[0]
            )

        # Add crossing data if the "show-crossings" checkbox is checked
        if "show" in show_crossings:
            fig_map.add_trace(
                px.scatter_mapbox(
                    crossing_data_filtered,
                    lat="Latitude",
                    lon="Longitude",
                    hover_name="City Name",  # Assuming City Name is a column in crossing_data
                    hover_data={
                        "Latitude": False,  # Hide latitude
                        "Longitude": False,  # Hide longitude
                        "Whistle Ban": True,
                        "Track Signaled": True,
                        "Number Of Bells": True,
                        "Traffic Lanes": True,
                        "Crossing Illuminated": True,
                    },
                ).update_traces(
                    marker=dict(size=max(5, min(20, 5 + (current_zoom * 1.5)) - (40 / (current_zoom + 3))),
                                color="#00FF00", symbol="circle", opacity=0.9),
                    hovertemplate="<b>%{hovertext}</b><br>"  # Display city name at the top
                                  "Whistle Ban: %{customdata[0]}<br>"
                                  "Track Signaled: %{customdata[1]}<br>"
                                  "Number Of Bells: %{customdata[2]}<br>"
                                  "Traffic Lanes: %{customdata[3]}<br>"
                                  "Crossing Illuminated: %{customdata[4]}<extra></extra>",
                    customdata=crossing_data_filtered[
                        ["Whistle Ban", "Track Signaled", "Number Of Bells", "Traffic Lanes", "Crossing Illuminated"]
                    ].values,
                ).data[0]
            )

        return fig_map, bar

    @app.callback(
        Output("visualization-container", "children"),
        [
            Input("viz-dropdown", "value"),
            Input("range-slider", "value"),
            Input("states-select", "value"),
        ],
    )
    def update_bottom_visual(selected_viz, selected_range, selected_states):

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
            return html.Div(
                'Oops! It seems like you haven’t selected a visualization. Pick one from the dropdown to see the magic!',
                id='no-viz-text',
                className='content',
                style={"textAlign": "center", "color": "gray", "fontSize": "16px"},
            )

        try:
            # ------------------ (1) Temporal Trends ------------------
            if selected_viz == "plot_1_1":
                # 1.1 Are total incidents increasing/decreasing over time?
                if "corrected_year" in dff.columns:
                    grouped = dff.groupby("DATE_M").size().reset_index(name="count_incidents")
                    fig = px.line(
                        grouped,
                        x="DATE_M",
                        y="count_incidents",
                        title="Total Incidents Over Time",
                        labels={
                            "DATE_M": "Incident Month",
                            "count_incidents": "Incident Count",
                        },
                    )
                    fig.update_traces(mode="lines+markers", line=dict(width=3))
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=100, l=20, r=20, b=20),
                        font=dict(size=14, color="white"),
                    )

            elif selected_viz == "plot_1_2":
                # 1.2 Which incident types show biggest changes over time?
                stream_graph = StreamGraph(aliases, dff, incident_types)
                fig = stream_graph.plot()

                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=100, l=20, r=20, b=20),
                    font=dict(size=14, color="white"),
                )

            elif selected_viz == "plot_1_3":
                # 1.3 Seasonal patterns => use the HeatMap class
                heatmap_plotter = HeatMap(aliases=aliases,
                                          df=dff)

                bin_size = 1
                fig = heatmap_plotter.create(bin_size=bin_size, states=selected_states)
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=100, l=20, r=20, b=20),
                    font=dict(size=14, color="white"),
                )

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
                    fig = px.sunburst(
                        grouped,
                        path=["state_name", "TYPE_LABEL"],  # Hierarchical path
                        values="count",
                        title="Top 10 States by Incident Count and Type",
                        color="count",
                        color_continuous_scale="Blues",
                    )
                    fig.update_traces(
                        hovertemplate="<b>%{label}</b><br>Count: %{value}",
                    )
                    # Update layout for better aesthetics
                    fig.update_layout(
                        margin=dict(t=100, l=20, r=20, b=20),
                        font=dict(size=14, color="white"),
                        paper_bgcolor="rgba(0,0,0,0)",
                    )

            elif selected_viz == "plot_2_3":
                # 2.3 Distribution differences => Parallel Categories Plot with selectable states
                if {"TYPE_LABEL", "ACCDMG", "WEATHER_LABEL", "TOTINJ", "TRNSPD", "state_name"}.issubset(dff.columns):
                    # Create bins for ACCDMG

                    bins_damage = [0, 1, 10000, 100000, 500000, df["ACCDMG"].max()]
                    labels_damage = ["No Damage", "1-10.000 $", "10.000-100.000 $", "100.000-500.000 $", "500.000+ $"]
                    dff["ACCDMG_Binned"] = pd.cut(dff["ACCDMG"], bins=bins_damage, labels=labels_damage,
                                                  include_lowest=True)

                    # Create bins for Injuries
                    bins_injuries = [0, 0.1, 1, 10, 20, df["TOTINJ"].max()]
                    labels_injuries = ["No Injuries", "0-1 Injuries", "1-10 Injuries", "11-20 Injuries", "21+ Injuries"]
                    dff["Injuries_Binned"] = pd.cut(dff["TOTINJ"], bins=bins_injuries, labels=labels_injuries,
                                                    include_lowest=True)

                    bins_damage = [0, 1, 10, 20, 50, 100, df["TRNSPD"].max()]
                    labels_damage = ["0 MPH", "1-10 MPH", "10-20 MPH", "20-50 MPH", "50-100 MPH", "100+ MPH"]
                    dff["TRNSPD_Binned"] = pd.cut(dff["TRNSPD"], bins=bins_damage, labels=labels_damage,
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
                    fig = px.parallel_categories(
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
                        title="Damage Distribution by Incident Type, Weather, and Injuries",
                    )
                    # Update layout for aesthetics
                    fig.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=100, l=150, r=50, b=20),
                        font=dict(size=14, color="white"),
                    )

            elif selected_viz == "plot_3_2":
                if "WEATHER_LABEL" in dff.columns and "TOTINJ" in dff.columns:
                    try:
                        # Instantiate the WeatherHeatMap class
                        heatmap_plotter = WeatherHeatMap(aliases=aliases, df=dff)
                        # Generate the heatmap figure
                        fig = heatmap_plotter.create()
                        # Apply consistent styling
                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            margin=dict(t=100, l=20, r=20, b=20),
                            font=dict(size=14, color="white"),
                        )
                        style_left = display_style

                    except Exception as e:
                        # Fallback for errors
                        fig = go.Figure()
                        fig.add_annotation(
                            text="An error occurred while generating the heatmap.",
                            showarrow=False,
                            font=dict(size=16, color="white"),
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            align="center",
                        )


                else:
                    # Fallback for missing required columns
                    fig = go.Figure()
                    fig.add_annotation(
                        text="Required columns 'WEATHER_LABEL' and 'TOTINJ' are missing in the DataFrame.",
                        showarrow=False,
                        font=dict(size=16, color="white"),
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                        align="center",
                    )



            elif selected_viz == "plot_3_3":
                needed = ["CAUSE", "CARS", "TOTINJ", "TOTKLD", "EVACUATE"]
                if all(n in dff.columns for n in needed):
                    # Map causes to categories
                    dff["CAUSE_CATEGORY"] = dff["CAUSE"].map(cause_category_mapping).fillna("Unknown")
                    # Group by cause category and aggregate additional factors
                    grouped = dff.groupby("CAUSE_CATEGORY")[
                        ["CARS", "TOTINJ", "TOTKLD", "EVACUATE"]].sum().reset_index()
                    # Melt the grouped data for visualization
                    melted = grouped.melt(
                        id_vars=["CAUSE_CATEGORY"],
                        value_vars=["CARS", "TOTINJ", "TOTKLD", "EVACUATE"],
                        var_name="Factor",
                        value_name="Value",
                    )
                    # Map factor names to more readable labels
                    factor_labels = {
                        "CARS": "Hazmat Cars Involved",
                        "TOTINJ": "Total Injuries",
                        "TOTKLD": "Total Fatalities",
                        "EVACUATE": "Persons Evacuated",
                    }
                    melted["Factor"] = melted["Factor"].map(factor_labels)
                    # Create the stacked bar chart
                    fig = px.bar(
                        melted,
                        x="CAUSE_CATEGORY",
                        y="Value",
                        color="Factor",
                        barmode="stack",
                        title="Factor Combos by Cause Category",
                        labels={
                            "CAUSE_CATEGORY": "Cause Category",
                            "Value": "Total Count",
                            "Factor": "Factor Type",
                        },
                    )
                    # Update layout for appearance
                    fig.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=100, l=20, r=20, b=20),
                        font=dict(size=14, color="white"),
                    )




            # ------------------ (4) Operator Performance ------------------
            elif selected_viz == "plot_4_1":
                # 4.1 Compare overall incident rates across operators => RAILROAD
                if "RAILROAD" in dff.columns:
                    rr_counts = dff["RAILROAD"].value_counts().nlargest(10).reset_index()
                    rr_counts.columns = ["RAILROAD", "count"]
                    fig = px.bar(
                        rr_counts,
                        x="RAILROAD",
                        y="count",
                        title="Top 10 Railroads by Incident Count",
                        labels={
                            "RAILROAD": "Reporting Railroad Code",
                            "count": "Count",
                        },
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=100, l=20, r=20, b=20),
                        font=dict(size=14, color="white"),
                    )




            elif selected_viz == "plot_4_2":
                # 4.2 Differences in incident types by operator => grouped bar
                if "RAILROAD" in dff.columns and "TYPE_LABEL" in dff.columns:
                    # Group data by railroad and type, and calculate the total count
                    grouped = (
                        dff.groupby(["RAILROAD", "TYPE_LABEL"])
                        .size()
                        .reset_index(name="count")
                    )
                    # Compute the total count per railroad
                    total_counts = grouped.groupby("RAILROAD")["count"].sum().reset_index()
                    # Select the top 10 railroads by total count
                    top_10_railroads = total_counts.nlargest(10, "count")["RAILROAD"]
                    # Filter the grouped data to include only the top 10 railroads
                    filtered_grouped = grouped[grouped["RAILROAD"].isin(top_10_railroads)]
                    # Create the grouped bar chart
                    fig = px.bar(
                        filtered_grouped,
                        x="RAILROAD",
                        y="count",
                        color="TYPE_LABEL",
                        barmode="group",
                        title="Incident Types by Top 10 Railroads",
                        labels={
                            "RAILROAD": "Reporting Railroad Code",
                            "TYPE_LABEL": "Incident Type",
                            "count": "Count",
                        },
                    )
                    # Update layout for appearance
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=100, l=20, r=20, b=20),
                        font=dict(size=14, color="white"),
                    )



            elif selected_viz == "plot_4_3":
                if "TYPE_LABEL" in dff.columns and "ACCDMG" in dff.columns:
                    try:
                        # Calculate the top 10 incident types by count
                        top_10_types = (
                            dff["TYPE_LABEL"]
                            .value_counts()
                            .nlargest(10)
                            .index
                        )
                        # Filter the data to include only the top 10 types
                        filtered_dff = dff[dff["TYPE_LABEL"].isin(top_10_types)]
                        # Sample the filtered data for better performance
                        sampled_df = filtered_dff.sample(frac=0.1, random_state=42)  # 10% sampling
                        # Create a violin plot
                        fig = px.violin(
                            sampled_df,
                            x="TYPE_LABEL",
                            y="ACCDMG",
                            box=True,  # Adds a box inside the violin for additional stats
                            points="all",  # Show all points (including outliers)
                            title="Damage Distribution by Top 10 Incident Types (Sampled Data)",
                            labels={
                                "TYPE_LABEL": "Incident Type",
                                "ACCDMG": "Damage Cost",
                            },
                        )
                        # Update layout for aesthetics
                        fig.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="white",
                            margin=dict(t=100, l=20, r=20, b=20),
                            font=dict(size=14, color="white"),
                        )
                        # Show the plot


                    except Exception as e:
                        print(f"Error processing plot_6_3: {e}")
                        # Return an empty figure with an error message annotation
                        fig = go.Figure()
                        fig.add_annotation(
                            text="An error occurred while generating the plot.",
                            showarrow=False,
                            font=dict(size=16, color="white"),
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            align="center",
                        )
                        # Still display the error message


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

                    fig = px.sunburst(
                        grouped,
                        path=["TYPE_LABEL", "CAUSE_CATEGORY", "CAUSE"],  # Hierarchical path
                        values="count",
                        title="Common Incident Types and Causes (Outliers by ACCDMG)",
                        color="count",
                        color_continuous_scale="Blues",
                    )

                    fig.update_traces(
                        hovertemplate=(
                            "<b>%{label}</b><br>"
                            "Count: %{value}<br>"
                            "Details: %{customdata}"
                            "<extra></extra>"
                        ),
                        customdata=grouped["CAUSE_INFO"],
                    )

                    fig.update_layout(
                        margin=dict(t=100, l=20, r=20, b=20),
                        font=dict(size=14, color="white"),
                        paper_bgcolor="rgba(0,0,0,0)",
                    )





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
                    fig = px.bar(
                        type_state_counts,
                        x="TYPE_LABEL",
                        y="count",
                        color="state_name",  # Use state_name to create the stacked effect
                        title="Most Common Incident Types by State",
                        labels={
                            "TYPE_LABEL": "Incident Type",
                            "count": "Count",
                            "state_name": "State",
                        },
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=100, l=20, r=20, b=20),
                        font=dict(size=14, color="white"),
                    )



            elif selected_viz == "plot_6_3":
                if "TYPE" in dff.columns and "ACCDMG" in dff.columns:
                    try:
                        sampled_df = dff.sample(frac=0.1, random_state=42)  # Use a subset of the data
                        # Create violin plot without filtering out outliers
                        fig = px.violin(
                            sampled_df,
                            x="TYPE_LABEL",
                            y="ACCDMG",
                            box=True,  # Adds a box inside the violin for additional stats
                            points="all",  # Show all points (including outliers)
                            title="Damage Distribution by Incident Type (Sampled Data)",
                            labels={
                                "TYPE_LABEL": "Incident Type",
                                "ACCDMG": "Damage Cost",
                            },
                        )
                        # Update layout for better aesthetics and responsive design
                        fig.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="white",
                            margin=dict(t=100, l=20, r=20, b=20),
                            font=dict(size=14, color="white"),
                        )
                        # Show the plot

                    except Exception as e:
                        print(f"Error processing plot_6_3: {e}")
                        # Return an empty figure with an error message annotation
                        fig = go.Figure()
                        fig.add_annotation(
                            text="An error occurred while generating the plot.",
                            showarrow=False,
                            font=dict(size=16, color="white"),
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            align="center",
                        )

                else:
                    # Fallback for missing columns
                    fig = go.Figure()
                    fig.add_annotation(
                        text="Required columns 'TYPE' and 'ACCDMG' are missing in the DataFrame.",
                        showarrow=False,
                        font=dict(size=16, color="white"),
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                        align="center",
                    )



        except Exception as e:
            print(f"Error creating visualization '{selected_viz}': {e}")

        return dcc.Graph(
            id="plot",
            className="content",
            config={"displayModeBar": False},
            style={"width": "100%", "height": "400px"},  # Ensure consistent sizing
            # Add your figure or data here:
            figure=fig,  # Replace with the actual figure for the selected visualization
        )
