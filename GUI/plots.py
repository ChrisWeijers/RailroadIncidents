import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd
from typing import Dict, Any, List, Optional
from GUI.config import US_POLYGON


class Map:
    """
    A class to create and manage an interactive choropleth map using Plotly and OpenStreetMap with OpenRailwayMap.
    """

    def __init__(
            self,
            df: pd.DataFrame,
            us_states: Dict[str, Any],
            state_count: pd.DataFrame,
            manual_zoom: Dict[str, Any]
    ) -> None:
        """
        Initializes the Map object with necessary data and initial zoom settings.
        """
        self.df = df
        self.us_states = us_states
        self.state_count = state_count
        self.manual_zoom = manual_zoom
        self.fig = go.Figure()
        self.state_coords = {}
        self._cache_state_geometries()

    def _cache_state_geometries(self) -> None:
        """Pre-compute state boundary coordinates."""
        if not hasattr(self, 'state_coords'):
            self.state_coords = {}

        for feature in self.us_states['features']:
            state_name = feature['properties']['name']
            geom = feature['geometry']

            if geom['type'] == 'Polygon':
                self.state_coords[state_name] = geom['coordinates'][0]
            elif geom['type'] == 'MultiPolygon':
                all_coords = []
                for polygon in geom['coordinates']:
                    all_coords.extend(polygon[0])
                    # Add (None, None) to break the shape in Plotly so each polygon is a separate outline
                    all_coords.append([None, None])
                self.state_coords[state_name] = all_coords

    def plot_map(self) -> go.Figure:
        """
        Generates a choropleth map of the United States, showing crash counts by state.
        """
        self.fig = go.Figure()

        # Color states by crash_count
        self.fig.add_trace(
            go.Choroplethmapbox(
                geojson=self.us_states,
                locations=self.state_count['state_name'],
                z=self.state_count['crash_count'],
                featureidkey="properties.name",
                colorscale=[[0, 'black'], [1, 'black']],
                marker_opacity=0.25,
                marker_line_width=0.5,
                marker_line_color='lightgrey',
                hoverinfo='text',
                customdata=self.state_count['state_name'],
                text=[
                    f"{s}<br>Crashes: {c:,}"
                    for s, c in zip(
                        self.state_count['state_name'],
                        self.state_count['crash_count']
                    )
                ],
                hovertemplate="<b>%{text}</b><extra></extra>",
                showscale=False,
                name='States',
            )
        )

        # Center & zoom from manual_zoom or defaults
        center = self.manual_zoom.get("center", {"lat": 39.8282, "lon": -98.5795})
        zoom = self.manual_zoom.get("zoom", 3)

        self.fig.update_layout(
            mapbox=dict(
                bounds={"west": -180, "east": -50, "south": 10, "north": 75},
                style="carto-darkmatter",
                center=center,
                zoom=zoom,
                layers=[
                    {
                        "below": 'traces',
                        "sourcetype": "raster",
                        "sourceattribution": (
                            'Style: <a href="https://creativecommons.org/licenses/by-sa/2.0/" target="_blank">'
                            'CC-BY-SA2.0</a> <a href="https://www.openrailwaymap.org/" target="_blank">'
                            'OpenRailwayMap</a>'
                        ),
                        "source": [
                            "https://tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png"
                        ],
                        "opacity": 0.8
                    }
                ]
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            paper_bgcolor='darkgrey',
            font=dict(color='white', size=12),
            showlegend=False,
        )
        return self.fig

    def add_points(self, df_state: pd.DataFrame, name: str) -> None:
        """
        Adds a density layer of points to the map (e.g., for incidences).
        """
        # Remove any existing densitymapbox layers first
        traces_to_remove = []
        for i, trace in enumerate(self.fig.data):
            if isinstance(trace, go.Densitymapbox):
                traces_to_remove.append(i)

        for i in reversed(traces_to_remove):
            self.fig.data = self.fig.data[:i] + self.fig.data[i + 1:]

        if df_state is not None and not df_state.empty:
            df_state = df_state.dropna(subset=['Latitude', 'Longitud'])

            if US_POLYGON is not None:
                # Filter out points outside the US polygon, if desired
                gdf = gpd.GeoDataFrame(
                    df_state,
                    geometry=gpd.points_from_xy(df_state['Longitud'], df_state['Latitude'])
                )
                gdf = gdf[gdf['geometry'].within(US_POLYGON)]
                df_state = pd.DataFrame(gdf.drop(columns='geometry'))

            if not df_state.empty:
                self.fig.add_trace(
                    go.Densitymapbox(
                        lat=df_state['Latitude'],
                        lon=df_state['Longitud'],
                        radius=3,
                        showscale=False,
                        hoverinfo='skip',
                        customdata=df_state['state_name'].tolist(),
                        name=name,
                        colorscale='Blues',
                    )
                )

    def highlight_state(self, hovered_state: str, trace_name: str) -> None:
        """Adds a highlight boundary for hovered or clicked state(s)."""

        # Remove existing highlights with the same trace_name
        traces_to_remove = []
        for i, trace in enumerate(self.fig.data):
            if trace.name == trace_name:
                traces_to_remove.append(i)
        for i in reversed(traces_to_remove):
            self.fig.data = self.fig.data[:i] + self.fig.data[i + 1:]

        # Convert to list if single string
        if isinstance(hovered_state, str):
            states_to_highlight = [hovered_state]
        elif isinstance(hovered_state, list):
            states_to_highlight = hovered_state
        else:
            return

        # Add highlight for each state
        for state in states_to_highlight:
            if state not in self.state_coords:
                continue

            coords = self.state_coords[state]
            lon = [coord[0] for coord in coords]
            lat = [coord[1] for coord in coords]
            self.fig.add_trace(
                go.Scattermapbox(
                    lon=lon,
                    lat=lat,
                    mode='lines',
                    line=dict(color='lightgrey', width=3),
                    hoverinfo='skip',
                    opacity=0.8,
                    name=trace_name,
                )
            )

        self.fig.update_layout(hovermode='closest')


class BarChart:
    """
    Simple horizontal bar chart for top-level state usage (number of crashes per state).
    """

    def __init__(self, df: pd.DataFrame, states_center: pd.DataFrame) -> None:
        self.df = df
        self.states_center = states_center
        self.bar = None
        self.states = None

    def create_barchart(self) -> go.Figure:
        self.bar = go.Figure()

        if "state_name" in self.df.columns:
            self.states = self.df["state_name"].value_counts().reset_index()
            self.states.columns = ["state_name", "count"]

            # If the data is extremely limited or empty, append the states_center to have minimal bars
            if len(self.df) < 2:
                # Which states are missing in self.states vs. states_center
                diff = pd.concat([self.states_center['Name'], self.states['state_name']]).drop_duplicates(keep=False)
                diff = diff.to_frame(name='state_name')
                diff['count'] = 0
                self.states = pd.concat([self.states, diff], ignore_index=True)

        self.bar.add_trace(
            go.Bar(
                x=self.states['count'],
                y=self.states['state_name'],
                text=self.states['state_name'],
                textposition='outside',
                orientation='h',
                marker=dict(color='white'),
                hovertemplate="<b>%{text}</b><br>Crashes: %{x:,}<extra></extra>",
            )
        )

        self.bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(r=0, t=0, l=0, b=0),
            yaxis=dict(showgrid=False, showticklabels=False, visible=False),
            xaxis=dict(showgrid=False, showticklabels=False, visible=False),
            font=dict(color="white", size=14, family="Helvetica"),
            hoverlabel=dict(
                bgcolor="lightgrey",
                bordercolor="grey",
                font=dict(size=14, color="black", family="Helvetica")
            ),
        )

        return self.bar


class HeatMap:
    """
    Generates a heatmap for visualizing temporal patterns of incident counts.
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame):
        self.df = df
        self.aliases = aliases

    def create(self, bin_size: int = 1, states: Optional[List[str]] = None) -> go.Figure:
        """
        Creates a heatmap with months on the y-axis and binned years on the x-axis,
        showing the total number of incidents.
        """
        dff = self.df.copy()
        if states:
            dff = dff[dff['state_name'].isin(states)]

        # We rely on 'corrected_year' and 'IMO' in dff
        if 'corrected_year' not in dff.columns or 'IMO' not in dff.columns:
            # Return an empty figure with an annotation if missing columns
            fig = go.Figure()
            fig.add_annotation(
                text="DataFrame must contain 'corrected_year' and 'IMO' columns for HeatMap.",
                showarrow=False,
                font=dict(size=16, color="white"),
                xref="paper", yref="paper", x=0.5, y=0.5, align="center",
            )
            return fig

        # Create year bins
        min_year = int(dff['corrected_year'].min())
        max_year = int(dff['corrected_year'].max())
        bins = list(range(min_year, max_year + bin_size, bin_size))
        if len(bins) < 2:
            # Not enough range to create bins
            bins = [min_year, min_year + 1]

        labels = [f"{bins[i]}" for i in range(len(bins) - 1)]
        dff['year_bin'] = pd.cut(
            dff['corrected_year'], bins=bins, right=False,
            labels=labels, include_lowest=True
        )

        # Group by month and year_bin
        heatmap_data = dff.groupby(['IMO', 'year_bin']).size().reset_index(name='incident_count')
        pivot_df = heatmap_data.pivot_table(
            index='IMO', columns='year_bin',
            values='incident_count', fill_value=0
        )

        # Convert the index from numeric months to names
        pivot_df.index = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]

        fig = px.imshow(
            pivot_df,
            labels=dict(x="Year Bin", y="Month", color="Incident Count"),
            title="Heatmap of Total Incidents by Month and Year",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=100, l=20, r=20, b=20),
            font=dict(size=14, color="white"),
        )
        return fig


class StreamGraph:
    """
    Generates a stream graph for visualizing how the amount of each incident type
    changes over time.
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame, incident_types: Dict[int, str]) -> None:
        self.aliases = aliases
        self.df = df
        self.incident_types = incident_types

    def plot(self) -> go.Figure:
        """
        Generates the stream graph figure.
        """
        df_plot = self.df.copy()
        df_plot['Incident Type Name'] = df_plot['TYPE'].map(self.incident_types)

        # Group by corrected_year + Incident Type
        if 'corrected_year' not in df_plot.columns:
            # Return empty figure if no 'corrected_year'
            return go.Figure()

        df_grouped = (
            df_plot.groupby(['corrected_year', 'Incident Type Name'])
            .size()
            .reset_index(name='Count')
        )

        incident_types = df_grouped['Incident Type Name'].unique()

        colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]

        fig = go.Figure()

        for idx, itype in enumerate(incident_types):
            color = colors[idx % len(colors)]
            df_type = df_grouped[df_grouped['Incident Type Name'] == itype].sort_values(by='corrected_year')

            fig.add_trace(
                go.Scatter(
                    x=df_type['corrected_year'],
                    y=df_type['Count'],
                    name=itype,
                    stackgroup='one',
                    mode='lines',
                    line=dict(width=0.5),
                    hoverinfo='x+y+name',
                    opacity=1,
                    fillcolor=color
                )
            )

        fig.update_layout(
            title='Incident Types Over Time',
            xaxis_title='Year',
            yaxis_title='Number of Incidents',
            hovermode='x unified',
            hoverlabel=dict(font_color="black", font_size=12, bgcolor="white"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white",
            margin=dict(t=100, l=20, r=20, b=20),
            font=dict(size=14, color="white"),
        )
        return fig


class WeatherHeatMap:
    """
    Generates a heatmap for visualizing injuries across weather conditions.
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame) -> None:
        self.df = df
        self.aliases = aliases

    def create(self) -> go.Figure:
        """
        Creates a heatmap with weather conditions on the x-axis and injury bins on the y-axis.
        Returns:
            A Plotly Figure object.
        """
        dff = self.df

        # Data validation checks
        if 'WEATHER_LABEL' not in dff.columns or 'TOTINJ' not in dff.columns:
            raise ValueError("DataFrame must contain 'WEATHER_LABEL' and 'TOTINJ' columns.")
        if dff.empty or dff['WEATHER_LABEL'].isnull().all() or dff['TOTINJ'].isnull().all():
            raise ValueError("No valid data in 'WEATHER_LABEL' or 'TOTINJ'.")

        # Bin injuries and prepare data
        bins = [0, 1, 10, 20, 50, float('inf')]
        bin_labels = ["0-1", "1-10", "10-20", "20-50", "50+"]
        dff['INJURY_BIN'] = pd.cut(dff['TOTINJ'], bins=bins, labels=bin_labels, right=False)

        heatmap_data = dff.groupby(['WEATHER_LABEL', 'INJURY_BIN']).size().reset_index(name='COUNT')
        pivot_df = heatmap_data.pivot_table(
            index='INJURY_BIN',
            columns='WEATHER_LABEL',
            values='COUNT',
            fill_value=0,
            observed=False
        )

        # Create visualization
        fig = px.imshow(
            pivot_df,
            labels={"color": "Incident Count"},
            title="Injury Severity by Weather Condition",
            color_continuous_scale=px.colors.sequential.Viridis,
            zmin=10,
            zmax=500
        )

        # Custom hover template
        fig.update_traces(
            hovertemplate=(
                "<b>Weather Condition</b>: %{x}<br>"
                "<b>Injury Range</b>: %{y}<br>"
                "<b>Total Incidents</b>: %{z}<extra></extra>"
            )
        )

        # Style configuration with axis labels
        fig.update_layout(
            margin=dict(t=100, l=20, r=20, b=20),
            font=dict(size=14, color="white"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Weather Conditions",  # X-axis label
            yaxis_title="Injury Severity",  # Y-axis label
            xaxis_title_font=dict(size=14),
            yaxis_title_font=dict(size=14),
            xaxis=dict(
                ticktext=[self.aliases.get(col, col) for col in pivot_df.columns],
                tickvals=pivot_df.columns
            ),
            yaxis=dict(
                ticktext=[f"{bin1} injuries" for bin1 in pivot_df.index],
                tickvals=pivot_df.index
            )
        )

        return fig


class CustomPlots:
    """
    A helper class that encapsulates all the custom visualizations (plot_1_1, plot_1_2, etc.)
    so that your Dash callbacks can simply call these methods.
    """

    def __init__(
            self,
            aliases: Dict[str, str],
            dff: pd.DataFrame,
            df: pd.DataFrame,
            selected_states: Optional[List[str]] = None,
    ):
        self.aliases = aliases
        self.dff = dff
        self.selected_states = selected_states
        self.df = df

    def plot_1_1(self) -> go.Figure:
        """
        1.1 Are total incidents increasing/decreasing over time?
        Group by 'DATE_M' and show a simple line chart of incident counts.
        """
        fig = go.Figure()
        dff = self.dff.copy()

        if "corrected_year" in dff.columns and "DATE_M" in dff.columns:
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
        else:
            fig.add_annotation(
                text="Columns 'corrected_year' or 'DATE_M' are missing.",
                showarrow=False,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                font=dict(size=16, color="white"),
            )

        return fig

    def plot_2_1(self) -> go.Figure:
        """
        2.1 Summarize top states + incident types with a sunburst.
        """
        fig = go.Figure()
        dff = self.dff.copy()

        if "state_name" in dff.columns and "TYPE_LABEL" in dff.columns:
            top_states = (
                dff["state_name"]
                .value_counts()
                .nlargest(10)
                .reset_index()
                .rename(columns={"index": "state_name", "state_name": "count"})
            )
            top_states.columns = ["state_name", "count"]

            # Filter data for these top states
            dff_top_states = dff[dff["state_name"].isin(top_states["state_name"])]

            grouped = (
                dff_top_states.groupby(["state_name", "TYPE_LABEL"])
                .size()
                .reset_index(name="count")
            )

            fig = px.sunburst(
                grouped,
                path=["state_name", "TYPE_LABEL"],
                values="count",
                title="Top 10 States by Incident Count and Type",
                color="count",
                color_continuous_scale="Blues",
            )
            fig.update_traces(
                hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>"
            )
            fig.update_layout(
                margin=dict(t=100, l=20, r=20, b=20),
                font=dict(size=14, color="white"),
                paper_bgcolor="rgba(0,0,0,0)",
            )
        else:
            fig.add_annotation(
                text="Columns 'state_name' or 'TYPE_LABEL' missing for plot_2_1.",
                showarrow=False,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                font=dict(size=16, color="white"),
            )
        return fig

    def plot_2_3(self) -> go.Figure:
        """
        2.3 Distribution differences => Parallel Categories Plot with selectable states
        """
        fig = go.Figure()
        dff = self.dff.copy()
        if self.selected_states:
            dff = dff[dff["state_name"].isin(self.selected_states)]

        needed_cols = {"TYPE_LABEL", "ACCDMG", "WEATHER_LABEL", "TOTINJ", "TRNSPD", "state_name"}
        if not needed_cols.issubset(dff.columns):
            fig.add_annotation(
                text="Missing columns for plot_2_3 parallel categories.",
                showarrow=False,
                x=0.5,
                y=0.5,
                font=dict(size=16, color="white")
            )
            return fig

        # Example: Binning logic
        bins_damage = [0, 1, 10000, 100000, 500000, self.df["ACCDMG"].max()]
        labels_damage = ["No Damage", "1-10.000 $", "10.000-100.000 $", "100.000-500.000 $", "500.000+ $"]
        dff["ACCDMG_Binned"] = pd.cut(dff["ACCDMG"], bins=bins_damage, labels=labels_damage, include_lowest=True)

        bins_injuries = [0, 0.1, 1, 10, 20, self.df["TOTINJ"].max()]
        labels_injuries = ["No Injuries", "0-1 Injuries", "1-10 Injuries", "11-20 Injuries", "21+ Injuries"]
        dff["Injuries_Binned"] = pd.cut(self.df["TOTINJ"], bins=bins_injuries, labels=labels_injuries,
                                        include_lowest=True)

        bins_speed = [0, 1, 10, 20, 50, 100, self.df["TRNSPD"].max()]
        labels_speed = ["0 MPH", "1-10 MPH", "10-20 MPH", "20-50 MPH", "50-100 MPH", "100+ MPH"]
        dff["TRNSPD_Binned"] = pd.cut(self.df["TRNSPD"], bins=bins_speed, labels=labels_speed, include_lowest=True)

        # Assign explicit colors if needed
        dff["state_color"] = dff["state_name"].apply(
            lambda x: "#FF0000" if x in (self.selected_states or []) else "#FF0000"
        )

        cols_for_plot = [
            "TYPE_LABEL", "WEATHER_LABEL", "ACCDMG_Binned",
            "Injuries_Binned", "TRNSPD_Binned", "state_color"
        ]
        dff_filtered = dff[cols_for_plot]

        fig = px.parallel_categories(
            dff_filtered,
            dimensions=[
                "TYPE_LABEL", "WEATHER_LABEL", "ACCDMG_Binned",
                "Injuries_Binned", "TRNSPD_Binned"
            ],
            color="state_color",
            labels={
                "TYPE_LABEL": "Incident Type",
                "ACCDMG_Binned": "Damage Category",
                "WEATHER_LABEL": "Weather Condition",
                "Injuries_Binned": "Injury Severity",
                "TRNSPD_Binned": "Train Speed",
                "state_color": "State Selection",
            },
            title="Damage Distribution by Incident Type, Weather, and Injuries"
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=100, l=150, r=50, b=20),
            font=dict(size=14, color="white"),
        )
        return fig

    def plot_3_3(self) -> go.Figure:
        """
        3.3 Factor combos => stacked bar for [CARS, TOTINJ, TOTKLD, EVACUATE] by cause category
        """
        fig = go.Figure()
        dff = self.dff.copy()
        needed = ["CAUSE", "CARS", "TOTINJ", "TOTKLD", "EVACUATE"]
        if not all(n in dff.columns for n in needed):
            fig.add_annotation(
                text="Missing columns for plot_3_3 stacked bar.",
                showarrow=False,
                x=0.5,
                y=0.5,
                font=dict(size=16, color="white")
            )
            return fig

        # Caller might pass in a cause_category_mapping; if you have that, you can do it here, or do a fallback
        # dff["CAUSE_CATEGORY"] = dff["CAUSE"].map(cause_category_mapping).fillna("Unknown")

        grouped = dff.groupby("CAUSE_CATEGORY")[["CARS", "TOTINJ", "TOTKLD", "EVACUATE"]].sum().reset_index()
        melted = grouped.melt(
            id_vars=["CAUSE_CATEGORY"],
            value_vars=["CARS", "TOTINJ", "TOTKLD", "EVACUATE"],
            var_name="Factor",
            value_name="Value"
        )
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
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=100, l=20, r=20, b=20),
            font=dict(size=14, color="white"),
        )
        return fig

    def plot_4_1(self) -> go.Figure:
        """
        4.1 Compare overall incident rates across operators => top 10 railroads
        """
        fig = go.Figure()
        dff = self.dff
        if "RAILROAD" not in dff.columns:
            fig.add_annotation(
                text="Missing 'RAILROAD' column for plot_4_1",
                showarrow=False,
                x=0.5,
                y=0.5,
                font=dict(size=16, color="white")
            )
            return fig

        rr_counts = dff["RAILROAD"].value_counts().nlargest(10).reset_index()
        rr_counts.columns = ["RAILROAD", "count"]
        fig = px.bar(
            rr_counts,
            x="RAILROAD",
            y="count",
            title="Top 10 Railroads by Incident Count",
            labels={"RAILROAD": "Reporting Railroad Code", "count": "Count"},
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=100, l=20, r=20, b=20),
            font=dict(size=14, color="white"),
        )
        return fig

    def plot_4_2(self) -> go.Figure:
        """
        4.2 Differences in incident types by operator => grouped bar
        """
        fig = go.Figure()
        dff = self.dff.copy()
        if "RAILROAD" in dff.columns and "TYPE_LABEL" in dff.columns:
            grouped = dff.groupby(["RAILROAD", "TYPE_LABEL"]).size().reset_index(name="count")
            total_counts = grouped.groupby("RAILROAD")["count"].sum().reset_index()
            top_10_rr = total_counts.nlargest(10, "count")["RAILROAD"]
            filtered_grouped = grouped[grouped["RAILROAD"].isin(top_10_rr)]

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
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=100, l=20, r=20, b=20),
                font=dict(size=14, color="white"),
            )
        else:
            fig.add_annotation(
                text="Missing 'RAILROAD' or 'TYPE_LABEL' for plot_4_2.",
                showarrow=False,
                x=0.5,
                y=0.5,
                font=dict(size=16, color="white")
            )
        return fig

    def plot_4_3(self) -> go.Figure:
        """
        4.3 A violin plot of ACCTDMG vs. TYPE_LABEL (top 10 types) or similar
        """
        fig = go.Figure()
        dff = self.dff.copy()
        if "TYPE_LABEL" in dff.columns and "ACCDMG" in dff.columns:
            try:
                top_10_types = dff["TYPE_LABEL"].value_counts().nlargest(10).index
                filtered_dff = dff[dff["TYPE_LABEL"].isin(top_10_types)]
                # For performance, sample 10%
                sampled_df = filtered_dff.sample(frac=0.1, random_state=42)

                fig = px.violin(
                    sampled_df,
                    x="TYPE_LABEL",
                    y="ACCDMG",
                    box=True,
                    points="all",
                    title="Damage Distribution by Top 10 Incident Types",
                    labels={
                        "TYPE_LABEL": "Incident Type",
                        "ACCDMG": "Damage Cost",
                    },
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    margin=dict(t=100, l=20, r=20, b=20),
                    font=dict(size=14, color="white"),
                )
            except Exception as e:
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Error in plot_4_3: {e}",
                    showarrow=False,
                    font=dict(size=16, color="white"),
                    xref="paper", yref="paper", x=0.5, y=0.5, align="center",
                )
        else:
            fig.add_annotation(
                text="Missing 'TYPE_LABEL' or 'ACCDMG' column for plot_4_3.",
                showarrow=False,
                x=0.5,
                y=0.5,
                font=dict(size=16, color="white")
            )
        return fig

    def plot_5_2(self, cause_category_mapping: dict, fra_cause_codes: dict) -> go.Figure:
        """
        Identifies outliers in ACCDMG, groups them by (TYPE_LABEL, CAUSE_CATEGORY, CAUSE, CAUSE_INFO),
        and shows a sunburst chart.
        """

        fig = go.Figure()
        needed = ["ACCDMG", "TYPE_LABEL", "CAUSE"]

        # Use self.df as the working DataFrame
        dff = self.dff.copy()

        # Ensure necessary columns exist
        if all(col in dff.columns for col in needed):
            # Calculate IQR and outlier threshold
            q1, q3 = dff["ACCDMG"].quantile([0.25, 0.75])
            iqr = q3 - q1
            outlier_threshold = q3 + 1.5 * iqr

            # Filter outliers
            outliers = dff[dff["ACCDMG"] > outlier_threshold]
            if outliers.empty:
                outliers = dff

            # Map cause to category
            outliers["CAUSE_CATEGORY"] = (
                outliers["CAUSE"].map(cause_category_mapping).fillna("Unknown")
            )

            # Map cause to descriptive text from nested dict
            outliers["CAUSE_INFO"] = outliers["CAUSE"].map(
                lambda x: next(
                    (
                        desc
                        for cat in fra_cause_codes.values()
                        for subcat in cat.values()
                        if isinstance(subcat, dict)
                        for code, desc in subcat.items()
                        if code == x
                    ),
                    "Unknown cause",
                )
            )

            # Group and count
            grouped = (
                outliers
                .groupby(["TYPE_LABEL", "CAUSE_CATEGORY", "CAUSE", "CAUSE_INFO"])
                .size()
                .reset_index(name="count")
            )

            # Sunburst
            fig = px.sunburst(
                grouped,
                path=["TYPE_LABEL", "CAUSE_CATEGORY", "CAUSE"],
                values="count",
                title="Common Incident Types and Causes",
                color="count",
                color_continuous_scale="Blues",
            )

            # Custom hover data
            fig.update_traces(
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Count: %{value}<br>"
                    "Details: %{customdata}"
                    "<extra></extra>"
                ),
                customdata=grouped["CAUSE_INFO"],
            )

            # Layout tweaks
            fig.update_layout(
                margin=dict(t=100, l=20, r=20, b=20),
                font=dict(size=14, color="white"),
                paper_bgcolor="rgba(0,0,0,0)",
            )

        else:
            fig.add_annotation(
                text="Missing columns for plot_5_2: ACCDMG, TYPE_LABEL, or CAUSE",
                showarrow=False,
                font=dict(size=16, color="white"),
                xref="paper", yref="paper", x=0.5, y=0.5
            )

        return fig

    def plot_6_1(self) -> go.Figure:
        """
        6.1 Most common incident types => stacked bar of state_name vs. TYPE_LABEL
        """
        fig = go.Figure()
        dff = self.dff.copy()
        if "TYPE_LABEL" in dff.columns and "state_name" in dff.columns:
            type_state_counts = dff.groupby(["TYPE_LABEL", "state_name"]).size().reset_index(name="count")
            top_types = (
                type_state_counts.groupby("TYPE_LABEL")["count"].sum().nlargest(10).index
            )
            type_state_counts = type_state_counts[type_state_counts["TYPE_LABEL"].isin(top_types)]

            fig = px.bar(
                type_state_counts,
                x="TYPE_LABEL",
                y="count",
                color="state_name",
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
        else:
            fig.add_annotation(
                text="Missing 'TYPE_LABEL' or 'state_name' columns for plot_6_1.",
                showarrow=False,
                x=0.5,
                y=0.5,
                font=dict(size=16, color="white")
            )
        return fig

    def plot_6_3(self) -> go.Figure:
        """
        6.3 Damage distribution by incident type (violin).
        """
        fig = go.Figure()
        dff = self.dff.copy()
        if "TYPE_LABEL" in dff.columns and "ACCDMG" in dff.columns:
            try:
                sampled_df = dff.sample(frac=0.1, random_state=42)
                fig = px.violin(
                    sampled_df,
                    x="TYPE_LABEL",
                    y="ACCDMG",
                    box=True,
                    points="all",
                    title="Damage Distribution by Incident Type",
                    labels={
                        "TYPE_LABEL": "Incident Type",
                        "ACCDMG": "Damage Cost",
                    },
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    margin=dict(t=100, l=20, r=20, b=20),
                    font=dict(size=14, color="white"),
                )
            except Exception as e:
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Error in plot_6_3: {e}",
                    showarrow=False,
                    x=0.5,
                    y=0.5,
                    font=dict(size=16, color="white")
                )
        else:
            fig.add_annotation(
                text="Missing 'TYPE_LABEL' or 'ACCDMG' column for plot_6_3.",
                showarrow=False,
                x=0.5,
                y=0.5,
                font=dict(size=16, color="white")
            )
        return fig
