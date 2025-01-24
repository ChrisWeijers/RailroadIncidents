from dash import Output, Input, State, callback_context, dcc, html, Dash
import pandas as pd
from typing import Dict, Any
from GUI.config import incident_types, weather, visibility, cause_category_mapping, fra_cause_codes
import plotly.express as px
import plotly.graph_objects as go
from GUI.plots import Map, BarChart, HeatMap, StreamGraph, WeatherHeatMap, CustomPlots


def setup_callbacks(
        app: Dash,
        df: pd.DataFrame,
        state_count: pd.DataFrame,
        us_states: Dict[str, Any],
        states_center,
        aliases: Dict[str, str],
        city_data: pd.DataFrame,
        crossing_data: pd.DataFrame,
):
    """
    Sets up all the callback functions for the Dash application.

    Args:
        app (Dash): The Dash application
        df (pd.DataFrame): The main DataFrame with accident data, cleaned and preprocessed.
        state_count (pd.DataFrame): DataFrame with crash counts per state.
        us_states (Dict[str, Any]): A dictionary containing the US states GeoJSON data.
        states_center (pd.DataFrame): DataFrame containing the latitude and longitude of the center of each state.
        aliases (Dict[str, str]): Dictionary containing all aliases for the data attributes.
        city_data (pd.Dataframe): Dataframe containing data about cities in the US.
        crossing_data (pd.Dataframe): Dataframe containing data about railroad crossing in the US.
    """

    def filter_by_range(df_local, selected_range):
        # Filter by corrected_year on the year range selected in the dashboard
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
    )
    def handle_selection(map_click, bar_click, dropdown_selected):
        """
        Updates the selected state(s) based barchart, map, and dropdown interaction.
        """

        # Keep track of what element is triggered
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        # Make sure dropdown_selected is a list
        if not isinstance(dropdown_selected, list):
            dropdown_selected = [dropdown_selected]

        # Add the selected state to the dropdown_selected list when clicking state on map or barchart
        if trigger_id == "crash-map" and map_click:
            point_data = map_click["points"][0]
            st = point_data.get("customdata") or point_data.get("text", "").split("<br>")[0]  # Get state
            if st and st not in dropdown_selected:
                dropdown_selected.append(st)
        elif trigger_id == "barchart" and bar_click:
            st = bar_click["points"][0].get("label") or bar_click["points"][0].get("x")  # Get state
            if st and st not in dropdown_selected:
                dropdown_selected.append(st)

        return dropdown_selected

    @app.callback(
        Output("hovered-state", "data"),
        [Input("crash-map", "hoverData"),
         Input("barchart", "hoverData")],
    )
    def handle_hover(map_hover, bar_hover):
        """
        Updates the hovered state.
        """

        # Keep track of what element is triggered
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        if trigger_id == "crash-map" and map_hover:
            pt = map_hover["points"][0]
            return pt.get("customdata") or pt.get("text", "").split("<br>")[0]  # Return the hovered state
        elif trigger_id == "barchart" and bar_hover:
            return bar_hover["points"][0].get("label") or bar_hover["points"][0].get("x")  # Return the hovered state
        return None  # Return None when no state is hovered

    @app.callback(
        [Output("crash-map", "figure"),
         Output("barchart", "figure")],
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
        Update the choropleth map and bar chart at the TOP based on state selection, hover, and date range.
        """

        # Filter the data on range selected
        df_filtered = filter_by_range(df, selected_range)

        # Create the map using the Map class
        us_map = Map(df_filtered, us_states, state_count, manual_zoom)
        fig_map = us_map.plot_map()

        # Create the barchart using the BarChart class
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
            # Filter the data if a state is selected, highlight the selected state(s) and add points belonging to state(s)
            us_map.highlight_state(selected_states, "clickstate")
            filtered_states = df_filtered[df_filtered["state_name"].isin(selected_states)]
            us_map.add_points(filtered_states, "clickstate")

            if len(selected_states) > 1:
                # Get barchart to change to only the selected states when more than 1 state is selected
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
                    marker=dict(
                        size=max(5, min(20, 5 + (current_zoom * 1.5)) - (40 / (current_zoom + 3))),
                        color="#DC267F",
                        symbol="circle",
                        opacity=0.9
                    ),
                ).data[0]
            )

        # Add crossing data if the "show-crossings" checkbox is checked
        if "show" in show_crossings:
            fig_map.add_trace(
                px.scatter_mapbox(
                    crossing_data_filtered,
                    lat="Latitude",
                    lon="Longitude",
                    hover_name="City Name",
                    hover_data={
                        "Latitude": False,
                        "Longitude": False,
                        "Whistle Ban": True,
                        "Track Signaled": True,
                        "Number Of Bells": True,
                        "Traffic Lanes": True,
                        "Crossing Illuminated": True,
                    },
                ).update_traces(
                    marker=dict(
                        # Change size of points depending on the zoom level
                        size=max(5, min(20, 5 + (current_zoom * 1.5)) - (40 / (current_zoom + 3))),
                        color="#009E73",
                        symbol="circle",
                        opacity=0.9
                    ),
                    hovertemplate=(  # The hover template
                        "<b>%{hovertext}</b><br>"
                        "Whistle Ban: %{customdata[0]}<br>"
                        "Track Signaled: %{customdata[1]}<br>"
                        "Number Of Bells: %{customdata[2]}<br>"
                        "Traffic Lanes: %{customdata[3]}<br>"
                        "Crossing Illuminated: %{customdata[4]}<extra></extra>"
                    ),
                    customdata=crossing_data_filtered[
                        ["Whistle Ban", "Track Signaled", "Number Of Bells", "Traffic Lanes", "Crossing Illuminated"]
                    ].values,
                ).data[0]
            )

        return fig_map, bar

    # ------------------ Callback for bottom visualization ------------------ #
    @app.callback(
        Output("visualization-container", "children"),
        [
            Input("viz-dropdown", "value"),
            Input("range-slider", "value"),
            Input("states-select", "value"),
        ],
    )
    def update_bottom_visual(selected_viz, selected_range, selected_states):
        """
        Update the visualization based on the selection of the dropdowns.
        """

        # Filter the data on the selected year range and the selected state(s)
        dff = filter_by_range(df.copy(), selected_range)
        if selected_states and "state_name" in dff.columns:
            dff = dff[dff["state_name"].isin(selected_states)]

        # Some label mappings used for certain plots
        dff["TYPE"] = dff["TYPE"].astype(int, errors='ignore')
        dff["TYPE_LABEL"] = dff["TYPE"].map(incident_types)
        dff["WEATHER_LABEL"] = dff["WEATHER"].map(weather).fillna(dff["WEATHER"])
        dff["VISIBLTY_LABEL"] = dff["VISIBLTY"].map(visibility).fillna(dff["VISIBLTY"])
        dff["CAUSE_CATEGORY"] = dff["CAUSE"].map(cause_category_mapping).fillna("Unknown")

        # If no visualization is selected return text
        if not selected_viz:
            return html.Div(
                'Oops! It seems like you haven’t selected a visualization. Pick one from the dropdown!',
                id='no-viz-text',
                className='content',
                style={"textAlign": "center", "color": "gray", "fontSize": "16px"},
            )

        # Instantiate our helper class for all custom plots
        custom_plots = CustomPlots(aliases, dff, df, selected_states)

        try:
            # Create the plot when selected

            if selected_viz == "plot_1_1":
                fig = custom_plots.plot_1_1()

            elif selected_viz == "plot_1_2":
                stream_graph = StreamGraph(aliases, dff, incident_types)
                fig = stream_graph.plot()

            elif selected_viz == "plot_1_3":
                heatmap_plotter = HeatMap(aliases=aliases, df=dff)
                fig = heatmap_plotter.create(bin_size=1, states=selected_states)

            elif selected_viz == "plot_2_1":
                fig = custom_plots.plot_2_1()

            elif selected_viz == "plot_2_3":
                fig = custom_plots.plot_2_3()

            elif selected_viz == "plot_3_2":
                try:
                    heatmap_plotter = WeatherHeatMap(aliases=aliases, df=dff)
                    fig = heatmap_plotter.create()

                except Exception as e:  # Show error when something went wrong
                    fig = go.Figure()
                    fig.add_annotation(
                        text=f"Error in WeatherHeatMap: {e}",
                        showarrow=False,
                        font=dict(size=16, color="white"),
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                        align="center",
                    )

            elif selected_viz == "plot_3_3":
                fig = custom_plots.plot_3_3()

            elif selected_viz == "plot_4_1":
                fig = custom_plots.plot_4_1()

            elif selected_viz == "plot_4_2":
                fig = custom_plots.plot_4_2()

            elif selected_viz == "plot_4_3":
                fig = custom_plots.plot_4_3()

            elif selected_viz == "plot_5_2":
                fig = custom_plots.plot_5_2(cause_category_mapping, fra_cause_codes)

            elif selected_viz == "plot_6_1":
                fig = custom_plots.plot_6_1()

            elif selected_viz == "plot_6_3":
                fig = custom_plots.plot_6_3()

            else:
                # Fallback if the dropdown selection doesn't match
                fig = go.Figure()
                fig.add_annotation(
                    text="No matching plot found.",
                    showarrow=False,
                    font=dict(size=16, color="white"),
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    align="center",
                )

        except Exception as e:  # Show error when something went wrong
            print(f"Error creating visualization '{selected_viz}': {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"An error occurred while generating the plot: {e}",
                showarrow=False,
                font=dict(size=16, color="white"),
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                align="center",
            )

        # Return the plot in a dcc.Graph element
        return dcc.Graph(
            id="plot",
            className="content",
            config={"displayModeBar": False},
            style={"width": "100%", "height": "100%"},
            figure=fig,
        )
