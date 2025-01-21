import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import geopandas as gpd
from GUI.config import US_POLYGON
import numpy as np



class Map:
    """
    A class to create and manage an interactive choropleth map using Plotly and OpenStreetMap with OpenRailwayMap.
    Useful if you want to add a second map in the bottom area as well,
    or do specialized mapping for (2) Spatial Patterns.
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
                    all_coords.append([None, None])
                self.state_coords[state_name] = all_coords

    def plot_map(self) -> go.Figure:
        """
        Generates a choropleth map of the United States, showing crash counts by state.
        """
        self.fig = go.Figure()

        # Basic approach: color states by crash_count
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
                        "sourceattribution": 'Style: <a href="https://creativecommons.org/licenses/by-sa/2.0/" '
                                             'target="_blank">CC-BY-SA2.0</a> <a '
                                             'href="https://www.openrailwaymap.org/" '
                                             'target="_blank">OpenRailwayMap</a>',
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
        Adds points/density to the map (e.g., for incidences).
        """
        # Remove any existing density points first
        self.fig.for_each_trace(
            lambda trace: trace.remove() if isinstance(trace, go.Densitymapbox) else None
        )

        if df_state is not None and not df_state.empty:
            df_state = df_state.dropna(subset=['Latitude', 'Longitud'])

            if US_POLYGON:  # If you have a polygon for the US
                gdf = gpd.GeoDataFrame(
                    df_state,
                    geometry=gpd.points_from_xy(df_state['Longitud'], df_state['Latitude'])
                )
                gdf = gdf[gdf['geometry'].within(US_POLYGON)]
                df_state = pd.DataFrame(gdf.drop(columns='geometry'))

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
        self.fig.for_each_trace(
            lambda trace: trace.remove() if trace.name == trace_name else None
        )

        # Handle both single state string and list of states
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
            self.fig.add_trace(
                go.Scattermapbox(
                    lon=[coord[0] for coord in coords],
                    lat=[coord[1] for coord in coords],
                    mode='lines',
                    line=dict(color='lightgrey', width=3),
                    hoverinfo='skip',
                    opacity=0.8,
                    name=trace_name,
                )
            )

        self.fig.update_layout(
            hovermode='closest',
        )


class BarChart:
    """
    Simple horizontal bar chart for the top-level state_count usage.
    """

    def __init__(self, df, states_center: pd.DataFrame) -> None:
        self.df = df
        self.states_center = states_center
        self.bar = None
        self.states = None

    def create_barchart(self) -> go.Figure:
        # Create the bar chart using go.Figure directly instead of px
        self.bar = go.Figure()

        if "state_name" in self.df.columns:
            self.states = self.df["state_name"].value_counts().reset_index()
            self.states.columns = ["state_name", "count"]
            if len(self.df) < 2:
                diff = pd.concat([self.states_center['Name'], self.states['state_name']]).drop_duplicates(
                    keep=False).to_frame()
                diff.columns = ['state_name']
                diff.insert(1, 'count', [0 for i in diff['state_name']])
                self.states = self.states._append(diff)

        self.bar.add_trace(
            go.Bar(
                x=self.states['count'],
                y=self.states['state_name'],
                text=self.states['state_name'],
                textposition='outside',
                orientation='h',
                marker=dict(
                    color='white',
                ),
                hovertemplate="<b>%{text}</b><br>Crashes: %{x:,}<extra></extra>",
            )
        )

        self.bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            yaxis=dict(
                showgrid=False,
                showticklabels=False,
                visible=False
            ),
            xaxis=dict(
                showgrid=False,
                showticklabels=False,
                visible=False
            ),
            font=dict(
                color="white",
                size=14,
                family="Helvetica"
            ),
            hoverlabel=dict(
                bgcolor="lightgrey",
                bordercolor="grey",
                font=dict(size=14, color="black", family="Helvetica")
            ),
        )

        return self.bar


class LineChart:
    """
    A line chart for time-series analysis (bullets 1.1, 1.2, 1.3, etc. where you want to see trends).
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def create(self, selected_states: List[str] = None) -> go.Figure:
        # Example grouping by year & month
        dff = self.df
        if selected_states:
            dff = dff[dff['state_name'].isin(selected_states)]

        # Basic example: group by year/month
        grouped = (
            dff.groupby(['year', 'month'])
            .size()
            .reset_index(name='count_incidents')
        )
        grouped['date'] = pd.to_datetime(
            grouped['year'].astype(str) + "-" + grouped['month'].astype(str).str.zfill(2) + "-01"
        )

        fig = px.line(
            grouped,
            x='date',
            y='count_incidents',
            title="Incidents Over Time",
        )
        fig.update_traces(mode="lines+markers", line=dict(color="white", width=2))

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white",
            margin=dict(l=40, r=20, t=40, b=20),
            showlegend=False,
            hovermode='x unified',
            transition={'duration': 500, 'easing': 'elastic-in-out'},
        )
        fig.update_xaxes(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            tickformat='%b %Y',
            tickangle=-45
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
        )
        return fig


class ScatterPlot:
    """
    Generic scatter plot with optional size or trendline. Great for bullets 3.1, 3.2, 3.3, etc.
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame):
        self.df = df
        self.aliases = aliases

    def create(self, x_attr: str, y_attr: str, states: List[str] = None) -> go.Figure:
        dff = self.df
        if states:
            dff = dff[dff['state_name'].isin(states)]

        fig = px.scatter(
            dff,
            x=x_attr,
            y=y_attr,
            color='state_name',
            title=f"Scatter: {self.aliases.get(x_attr, x_attr)} vs. {self.aliases.get(y_attr, y_attr)}",
            labels={
                x_attr: self.aliases.get(x_attr, x_attr),
                y_attr: self.aliases.get(y_attr, y_attr),
            }
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def create_with_size(
            self, x_attr: str, y_attr: str, size_attr: str, states: List[str] = None
    ) -> go.Figure:
        dff = self.df
        if states:
            dff = dff[dff['state_name'].isin(states)]

        fig = px.scatter(
            dff,
            x=x_attr,
            y=y_attr,
            size=size_attr,
            color='state_name',
            title=(
                f"Scatter: {self.aliases.get(x_attr, x_attr)} vs. "
                f"{self.aliases.get(y_attr, y_attr)} (size={self.aliases.get(size_attr, size_attr)})"
            ),
            labels={
                x_attr: self.aliases.get(x_attr, x_attr),
                y_attr: self.aliases.get(y_attr, y_attr),
                size_attr: self.aliases.get(size_attr, size_attr),
            }
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def create_with_trendline(
            self, x_attr: str, y_attr: str, trendline: str = "ols", states: List[str] = None
    ) -> go.Figure:
        dff = self.df
        if states:
            dff = dff[dff['state_name'].isin(states)]

        fig = px.scatter(
            dff,
            x=x_attr,
            y=y_attr,
            color='state_name',
            trendline=trendline,
            title=(
                f"Scatter + Trendline: {self.aliases.get(x_attr, x_attr)} vs. "
                f"{self.aliases.get(y_attr, y_attr)}"
            ),
            labels={
                x_attr: self.aliases.get(x_attr, x_attr),
                y_attr: self.aliases.get(y_attr, y_attr),
            }
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig


class HeatMap:
    """
    Generates a heatmap for visualizing temporal patterns of incident counts.
    """
    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame):
        self.df = df
        self.aliases = aliases

    def create(self, bin_size: int = 10, states: List[str] = None) -> go.Figure:
        """
        Creates a heatmap with months on the y-axis and binned years on the x-axis,
        showing the total number of incidents.

        Args:
            bin_size: The number of years to group into each bin.
            states: Optional list of state names to filter the data.

        Returns:
            A Plotly Figure object.
        """
        dff = self.df
        if states:
            dff = dff[dff['state_name'].isin(states)]

        # Ensure 'corrected_year' and 'IMO' (month) are present
        if 'corrected_year' not in dff.columns or 'IMO' not in dff.columns:
            raise ValueError("DataFrame must contain 'corrected_year' and 'IMO' columns.")

        # Create year bins
        min_year = dff['corrected_year'].min()
        max_year = dff['corrected_year'].max()
        bins = list(range(min_year, max_year + bin_size, bin_size))
        labels = [f"{bins[i]}" for i in range(len(bins)-1)]
        dff['year_bin'] = pd.cut(dff['corrected_year'], bins=bins, right=False, labels=labels, include_lowest=True)

        # Group by month and year bin and count the incidents using .size()
        heatmap_data = dff.groupby(['IMO', 'year_bin']).size().reset_index(name='incident_count')

        # Pivot the data for the heatmap
        pivot_df = heatmap_data.pivot_table(index='IMO', columns='year_bin', values='incident_count', fill_value=0)

        # Rename index to month names
        pivot_df.index = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]

        fig = px.imshow(
            pivot_df,
            labels=dict(x="Year Bin", y="Month", color="Incident Count"),
            title=f"Heatmap of Total Incidents by Month and Year Bin (Bin Size: {bin_size} years)",
            color_continuous_scale=px.colors.sequential.Viridis  # You can choose a different color scale
        )

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig
class WeatherHeatMap:
    """
    Generates a heatmap for visualizing injuries across weather conditions.
    """
    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame):
        self.df = df
        self.aliases = aliases

    def create(self) -> go.Figure:
        """
        Creates a heatmap with weather conditions on the x-axis and injury bins on the y-axis.

        Returns:
            A Plotly Figure object.
        """
        dff = self.df

        # Ensure required columns are present
        if 'WEATHER_LABEL' not in dff.columns or 'TOTINJ' not in dff.columns:
            raise ValueError("DataFrame must contain 'WEATHER_LABEL' and 'TOTINJ' columns.")

        # Check for empty or missing data
        if dff.empty or dff['WEATHER_LABEL'].isnull().all() or dff['TOTINJ'].isnull().all():
            raise ValueError("No valid data in 'WEATHER_LABEL' or 'TOTINJ'.")

        # Define bins for injuries
        bins = [0, 1, 10, 20, 50, float('inf')]
        bin_labels = ["0-1", "1-10", "10-20", "20-50", "50+"]
        dff['INJURY_BIN'] = pd.cut(dff['TOTINJ'], bins=bins, labels=bin_labels, right=False)

        # Group data by weather condition and injury bin
        heatmap_data = dff.groupby(['WEATHER_LABEL', 'INJURY_BIN']).size().reset_index(name='COUNT')

        # Pivot data for the heatmap
        pivot_df = heatmap_data.pivot_table(
            index='INJURY_BIN',
            columns='WEATHER_LABEL',
            values='COUNT',
            fill_value=0
        )

        # Create heatmap using Plotly
        fig = px.imshow(
            pivot_df,
            labels={
                "x": "Weather Condition",
                "y": "Injury Bins",
                "color": "Count",
            },
            title="Heatmap of Injury Bins by Weather Condition",
            color_continuous_scale=px.colors.sequential.Viridis,
            zmin=10,  # Set minimum for better visibility of smaller counts
            zmax=500  # Cap maximum to reduce dominance of extreme values
        )

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig




class StreamGraph:
    """
    Generates a stream graph for visualizing the amount of incident types over time.
    """
    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame, incident_types: Dict[int, str]) -> None:
        self.aliases = aliases
        self.df = df
        self.incident_types = incident_types

    def plot(self):
        """
        Generates the stream graph.
        """
        df_plot = self.df.copy()
        df_plot['Incident Type Name'] = df_plot['TYPE'].map(self.incident_types)

        # Group by year and incident type, counting occurrences
        df_grouped = df_plot.groupby(['corrected_year', 'Incident Type Name']).size().reset_index(name='Count')

        # Get unique incident types for creating traces
        incident_types = df_grouped['Incident Type Name'].unique()

        colors = [
            '#1f77b4',  # blue
            '#ff7f0e',  # orange
            '#2ca02c',  # green
            '#d62728',  # red
            '#9467bd',  # purple
            '#8c564b',  # brown
            '#e377c2',  # pink
            '#7f7f7f',  # gray
            '#bcbd22',  # yellow-green
            '#17becf',  # cyan
            '#ff9896',  # light red
            '#98df8a',  # light green
            '#c5b0d5'  # light purple
        ]

        fig = go.Figure()

        for idx, incident_type in enumerate(incident_types):
            # Use modulo to cycle through colors if there are more incident types than colors
            color = colors[idx % len(colors)]

            df_type = df_grouped[df_grouped['Incident Type Name'] == incident_type].sort_values(by='corrected_year')
            fig.add_trace(go.Scatter(
                x=df_type['corrected_year'],
                y=df_type['Count'],
                name=incident_type,
                stackgroup='one',
                mode='lines',
                line=dict(width=0.5),
                hoverinfo='x+y+name',
                opacity=1,
                fillcolor=color  # Add this line to set the fill color
            ))

        fig.update_layout(
            title='Incident Types Over Time',
            xaxis_title='Incident Year',
            yaxis_title='Number of Incidents',
            hovermode='x unified',
            hoverlabel=dict(
                font_color="black",
                font_size=12,
                bgcolor="white"
            )
        )
        return fig


class ParallelCategoriesPlot:
    """
    A class to create and manage parallel categories plots for accident data visualization.

    Attributes:
        required_columns (set): Set of required columns in the input DataFrame
        damage_bins (list): Bin edges for accident damage categories
        damage_labels (list): Labels for damage categories
        injuries_bins (list): Bin edges for injury categories
        injuries_labels (list): Labels for injury categories
        speed_bins (list): Bin edges for speed categories
        speed_labels (list): Labels for speed categories
    """

    def __init__(self):
        """Initialize the ParallelCategoriesPlot with predefined bin ranges and labels."""
        self.required_columns = {
            "TYPE_LABEL", "ACCDMG", "WEATHER_LABEL",
            "TOTINJ", "TRNSPD", "state_name"
        }

        # Define bins and labels for different categories
        self.damage_bins = [0, 100000, 500000, 1000000, 5000000]  # Last bin will be added dynamically
        self.damage_labels = [
            "Low Damage", "Moderate Damage", "High Damage",
            "Severe Damage", "Extreme Damage"
        ]

        self.injuries_bins = [0, 1, 5, 10, 20]  # Last bin will be added dynamically
        self.injuries_labels = [
            "No Injuries", "1-5 Injuries", "6-10 Injuries",
            "11-20 Injuries", "21+ Injuries"
        ]

        self.speed_bins = [0, 10, 30, 50, 70, 100]  # Last bin will be added dynamically
        self.speed_labels = [
            "Very Slow", "Slow", "Moderate", "Fast",
            "Very Fast", "Extremely Fast"
        ]

    def _validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate that the input DataFrame contains all required columns.

        Args:
            df: Input DataFrame to validate

        Returns:
            bool: True if all required columns are present, False otherwise
        """
        return self.required_columns.issubset(df.columns)

    def _create_binned_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create binned columns for damage, injuries, and speed.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with additional binned columns
        """
        df = df.copy()

        # Add maximum values to bins
        damage_bins = self.damage_bins + [float(df["ACCDMG"].max())]
        injuries_bins = self.injuries_bins + [float(df["TOTINJ"].max())]
        speed_bins = self.speed_bins + [float(df["TRNSPD"].max())]

        # Create binned columns
        df["ACCDMG_Binned"] = pd.cut(
            df["ACCDMG"],
            bins=damage_bins,
            labels=self.damage_labels,
            include_lowest=True
        )

        df["Injuries_Binned"] = pd.cut(
            df["TOTINJ"],
            bins=injuries_bins,
            labels=self.injuries_labels,
            include_lowest=True
        )

        df["TRNSPD_Binned"] = pd.cut(
            df["TRNSPD"],
            bins=speed_bins,
            labels=self.speed_labels,
            include_lowest=True
        )

        return df

    def _assign_state_colors(
            self,
            df: pd.DataFrame,
            selected_states: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Assign colors to states based on selection.

        Args:
            df: Input DataFrame
            selected_states: List of selected state names

        Returns:
            DataFrame with state_color column added
        """
        df = df.copy()

        if selected_states:
            mask = df["state_name"].isin(selected_states)
            df["state_color"] = np.where(mask, "#FF0000", "#0000FF")
        else:
            df["state_color"] = "#0000FF"

        return df

    def create_plot(
            self,
            df: pd.DataFrame,
            selected_states: Optional[List[str]] = None,
            display_style: Dict = None,
            hidden_style: Dict = None
    ):
        """
        Create a parallel categories plot based on the input data.

        Args:
            df: Input DataFrame containing accident data
            selected_states: List of selected state names
            display_style: Dictionary containing display style settings
            hidden_style: Dictionary containing hidden style settings

        Returns:
            Tuple containing:
            - Plotly figure object
            - Style dictionary for left component
            - Style dictionary for right component
        """
        try:
            if not self._validate_data(df):
                raise ValueError("Missing required columns in DataFrame")

            # Process data
            df = self._create_binned_columns(df)
            df = self._assign_state_colors(df, selected_states)

            # Filter data if states are selected
            if selected_states and len(df[df["state_name"].isin(selected_states)]) == 0:
                fig = px.scatter(title="No data available for selected states")
            else:
                # Prepare data for plotting
                plot_columns = [
                    "TYPE_LABEL", "WEATHER_LABEL", "ACCDMG_Binned",
                    "Injuries_Binned", "TRNSPD_Binned", "state_color"
                ]
                df_filtered = df[plot_columns]

                # Create plot
                title = ("Damage Distribution Analysis for "
                         f"{', '.join(selected_states)}" if selected_states else
                         "Overall Damage Distribution Analysis")

                fig = px.parallel_categories(
                    df_filtered,
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
                    title=title
                )

            # Update layout
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
            )

            return fig, display_style or {}, hidden_style or {}

        except Exception as e:
            print(f"Error in parallel categories plot: {str(e)}")
            fig = px.scatter(title="Error generating parallel categories plot")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
            )
            return fig, display_style or {}, hidden_style or {}


class GroupedBarChart:
    """
    Great for comparing categories across a second grouping dimension (e.g., year, incident type, operator).
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame):
        self.df = df
        self.aliases = aliases

    def create(
            self,
            x_attr: str,
            y_attr: str,
            group_attr: str = None,
            states: List[str] = None
    ) -> go.Figure:
        dff = self.df
        if states:
            dff = dff[dff['state_name'].isin(states)]

        # If we have a grouping dimension, do grouped bar; else a basic bar
        if group_attr and group_attr in dff.columns:
            fig = px.bar(
                dff,
                x=x_attr,
                y=y_attr,
                color=group_attr,
                barmode='group',
                labels={
                    x_attr: self.aliases.get(x_attr, x_attr),
                    y_attr: self.aliases.get(y_attr, y_attr),
                    group_attr: self.aliases.get(group_attr, group_attr),
                },
            )
            fig.update_layout(title=f"Grouped Bar: {y_attr} by {x_attr} & {group_attr}")
        else:
            fig = px.bar(
                dff,
                x=x_attr,
                y=y_attr,
                labels={
                    x_attr: self.aliases.get(x_attr, x_attr),
                    y_attr: self.aliases.get(y_attr, y_attr),
                },
            )
            fig.update_layout(title=f"Bar: {y_attr} by {x_attr}")

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig


class ClusteredBarChart:
    """
    Similar to GroupedBarChart but we keep it separate in case you need different logic or style.
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame):
        self.df = df
        self.aliases = aliases

    def create(
            self,
            x_attr: str,
            y_attr: str,
            cluster_attr: str = None,
            states: List[str] = None
    ) -> go.Figure:
        dff = self.df
        if states:
            dff = dff[dff['state_name'].isin(states)]

        if cluster_attr and cluster_attr in dff.columns:
            fig = px.bar(
                dff,
                x=x_attr,
                y=y_attr,
                color=cluster_attr,
                barmode='group',
                labels={
                    x_attr: self.aliases.get(x_attr, x_attr),
                    y_attr: self.aliases.get(y_attr, y_attr),
                    cluster_attr: self.aliases.get(cluster_attr, cluster_attr),
                },
            )
            fig.update_layout(
                title=f"Clustered Bar: {y_attr} by {x_attr} & {cluster_attr}"
            )
        else:
            fig = px.bar(
                dff,
                x=x_attr,
                y=y_attr,
                labels={
                    x_attr: self.aliases.get(x_attr, x_attr),
                    y_attr: self.aliases.get(y_attr, y_attr),
                },
            )
            fig.update_layout(title=f"Bar: {y_attr} by {x_attr}")

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig


class StackedBarChart:
    """
    Good for part-to-whole relationships: e.g. "damage components" or "incident counts by type" stacked.
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame):
        self.df = df
        self.aliases = aliases

    def create(self, category_col: str, damage_cols: List[str]) -> go.Figure:
        # 'damage_cols' can be any set of numeric columns to stack up
        dff = self.df.copy()
        melted = dff.melt(
            id_vars=[category_col],
            value_vars=damage_cols,
            var_name='StackType',
            value_name='StackValue'
        )
        fig = px.bar(
            melted,
            x=category_col,
            y='StackValue',
            color='StackType',
            barmode='stack',
            labels={
                category_col: self.aliases.get(category_col, category_col),
                'StackType': 'Category',
                'StackValue': 'Value',
            },
        )
        col_list = ', '.join(damage_cols)
        fig.update_layout(
            title=f"Stacked: {col_list} by {category_col}",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig


class BoxPlot:
    """
    Box plots can reveal distributions (outliers, median, quartiles).
    Could be used for analyzing how e.g. 'train speed' or 'damage' is distributed across categories.
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame):
        self.df = df
        self.aliases = aliases

    def create(self, x_attr: str, y_attr: str, states: List[str] = None) -> go.Figure:
        dff = self.df
        if states:
            dff = dff[dff['state_name'].isin(states)]

        fig = px.box(
            dff,
            x=x_attr,
            y=y_attr,
            color=x_attr,
            labels={
                x_attr: self.aliases.get(x_attr, x_attr),
                y_attr: self.aliases.get(y_attr, y_attr),
            },
        )
        fig.update_layout(
            title=f"Box Plot of {y_attr} by {x_attr}",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig


class PieChart:
    """
    If you want to show distribution of categories in a donut/pie form.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def create(self, category: str, top_n: int = 10, states: List[str] = None) -> go.Figure:
        dff = self.df
        if states:
            dff = dff[dff['state_name'].isin(states)]

        cat_counts = (
            dff[category]
            .value_counts()
            .nlargest(top_n)
            .reset_index()
        )
        cat_counts.columns = ['category', 'count']

        fig = px.pie(
            cat_counts,
            names='category',
            values='count',
            hole=0.4,  # donut
        )
        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>%{percent:.1%}<extra></extra>",
        )
        fig.update_layout(
            title=f"Top {top_n} categories in {category}",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white",
            legend=dict(font=dict(color='white'), bgcolor='rgba(0,0,0,0)')
        )
        return fig


class DomainPlots:
    """
    A class with 18 methods, each returning a Plotly figure for a specific
    domain question (1.1 through 6.3). We rely on:

      - 'corrected_year' instead of YEAR
      - 'IMO' for month
      - 'aliases' dict for labeling
      - typical columns like 'TYPE', 'CAUSE', 'CAUSE2', 'RAILROAD', 'ACCDMG', 'TOTINJ', 'CARS', etc.
      - 'state_name' for state-level analysis (if available)
    """

    def __init__(self, df: pd.DataFrame, aliases: Dict[str, str]):
        self.df = df.copy()
        self.aliases = aliases

    # --------------- (1) Analyzing Temporal Trends ---------------
    def plot_1_1_incidents_over_time(self) -> go.Figure:
        """
        1.1: Are total incidents increasing/decreasing over time?
        => line chart grouped by corrected_year
        """
        if "corrected_year" not in self.df.columns:
            return go.Figure()

        grouped = (
            self.df.groupby("corrected_year")
            .size()
            .reset_index(name="count_incidents")
        )
        fig = px.line(
            grouped,
            x="corrected_year",
            y="count_incidents",
            title="Total Incidents Over Time",
            labels={
                "corrected_year": self.aliases.get("corrected_year", "Year"),
                "count_incidents": "Incident Count",
            },
        )
        fig.update_traces(mode="lines+markers", line=dict(width=3))
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_1_2_types_biggest_changes(self) -> go.Figure:
        """
        1.2: Which incident types show biggest changes over time?
        => multi-line chart by (corrected_year, TYPE)
        """
        if "corrected_year" not in self.df.columns or "TYPE" not in self.df.columns:
            return go.Figure()

        grouped = (
            self.df.groupby(["corrected_year", "TYPE"])
            .size()
            .reset_index(name="count_incidents")
        )
        fig = px.line(
            grouped,
            x="corrected_year",
            y="count_incidents",
            color="TYPE",
            title="1.2 Incident Types Over Time",
            labels={
                "corrected_year": self.aliases.get("corrected_year", "Year"),
                "TYPE": self.aliases.get("TYPE", "Type"),
                "count_incidents": "Incident Count",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_1_3_seasonal_patterns(self) -> go.Figure:
        """
        1.3: Any noticeable seasonal patterns?
        => bar chart grouped by month 'IMO'
        """
        if "IMO" not in self.df.columns:
            return go.Figure()

        grouped = self.df.groupby("IMO").size().reset_index(name="count_incidents")
        fig = px.bar(
            grouped,
            x="IMO",
            y="count_incidents",
            title="1.3 Seasonal Patterns by Month (IMO)",
            labels={
                "IMO": self.aliases.get("IMO", "Month"),
                "count_incidents": "Incident Count",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    # --------------- (2) Spatial Patterns ---------------
    def plot_2_1_highest_geo_concentration(self) -> go.Figure:
        """
        2.1: Highest geographic concentration of incidents?
        => top 10 states (state_name) in a pie or bar
        """
        if "state_name" not in self.df.columns:
            return go.Figure()

        top_states = self.df["state_name"].value_counts().nlargest(10).reset_index()
        top_states.columns = ["state_name", "count"]
        fig = px.pie(
            top_states,
            names="state_name",
            values="count",
            title="2.1 Top 10 States by Incident Count",
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_2_2_geo_factors_vs_incident_rates(self) -> go.Figure:
        """
        2.2: Geographic factors (urban, mountains) vs. incident rates?
        If you have columns for that, use them.
        Otherwise, as a placeholder, let's do a bar of 'state_name' if we have it.
        """
        if "state_name" not in self.df.columns:
            return go.Figure()

        # just do a bar of total incidents by state_name
        grouped = self.df["state_name"].value_counts().reset_index()
        grouped.columns = ["state_name", "count"]
        fig = px.bar(
            grouped,
            x="state_name",
            y="count",
            title="2.2 (Placeholder) Incidents by State",
            labels={
                "state_name": "State",
                "count": "Incident Count",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_2_3_distribution_diff_incident_types(self) -> go.Figure:
        """
        2.3: Distribution differences for various incident types
        => e.g. box plot x=TYPE, y=ACCDMG
        """
        if "TYPE" not in self.df.columns or "ACCDMG" not in self.df.columns:
            return go.Figure()

        fig = px.box(
            self.df,
            x="TYPE",
            y="ACCDMG",
            title="2.3 Damage Distribution by Incident Type",
            labels={
                "TYPE": self.aliases.get("TYPE", "Type"),
                "ACCDMG": self.aliases.get("ACCDMG", "Damage Cost"),
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    # --------------- (3) Contributing Factors ---------------
    def plot_3_1_factors_correlate_strongly(self) -> go.Figure:
        """
        3.1: Which factors (speed, weather, track) correlate strongly?
        => scatter x=TRNSPD, y=ACCDMG, color=WEATHER (if exist)
        """
        needed = ["TRNSPD", "ACCDMG", "WEATHER"]
        if not all(n in self.df.columns for n in needed):
            return go.Figure()

        fig = px.scatter(
            self.df,
            x="TRNSPD",
            y="ACCDMG",
            color="WEATHER",
            title="3.1 Speed vs. Damage, colored by Weather",
            labels={
                "TRNSPD": self.aliases.get("TRNSPD", "Train Speed"),
                "ACCDMG": self.aliases.get("ACCDMG", "Damage Cost"),
                "WEATHER": self.aliases.get("WEATHER", "Weather"),
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_3_2_factors_affect_severity(self) -> go.Figure:
        """
        3.2: How do these factors affect severity (damage, injuries)?
        => box: x=WEATHER, y=TOTINJ
        """
        needed = ["WEATHER", "TOTINJ"]
        if not all(n in self.df.columns for n in needed):
            return go.Figure()

        fig = px.box(
            self.df,
            x="WEATHER",
            y="TOTINJ",
            title="3.2 Weather vs. Total Injuries",
            labels={
                "WEATHER": self.aliases.get("WEATHER", "Weather"),
                "TOTINJ": self.aliases.get("TOTINJ", "Total Injuries"),
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_3_3_factor_combos(self) -> go.Figure:
        """
        3.3: Specific factor combos that precede incidents?
        => stacked bar: CAUSE x [CARS, TOTINJ]
        """
        needed = ["CAUSE", "CARS", "TOTINJ"]
        for col in needed:
            if col not in self.df.columns:
                return go.Figure()

        melted = self.df.melt(
            id_vars=["CAUSE"],
            value_vars=["CARS", "TOTINJ"],
            var_name="Factor",
            value_name="Value"
        )
        fig = px.bar(
            melted,
            x="CAUSE",
            y="Value",
            color="Factor",
            barmode="stack",
            title="3.3 Factor Combos by Cause",
            labels={
                "CAUSE": "Cause",
                "Value": "Count/Value",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    # --------------- (4) Operator Performance ---------------
    def plot_4_1_incident_rates_across_operators(self) -> go.Figure:
        """
        4.1: Compare overall incident rates across operators => RAILROAD
        => bar top 10
        """
        if "RAILROAD" not in self.df.columns:
            return go.Figure()

        rr_counts = self.df["RAILROAD"].value_counts().nlargest(10).reset_index()
        rr_counts.columns = ["RAILROAD", "count"]
        fig = px.bar(
            rr_counts,
            x="RAILROAD",
            y="count",
            title="4.1 Top 10 Railroads by Incident Count",
            labels={
                "RAILROAD": self.aliases.get("RAILROAD", "Operator"),
                "count": "Incident Count",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_4_2_differences_incident_types_by_operator(self) -> go.Figure:
        """
        4.2: Differences in incident types by operator => grouped bar
        => group by (RAILROAD, TYPE)
        """
        needed = ["RAILROAD", "TYPE"]
        if not all(n in self.df.columns for n in needed):
            return go.Figure()

        grouped = (
            self.df.groupby(["RAILROAD", "TYPE"])
            .size()
            .reset_index(name="count")
        )
        fig = px.bar(
            grouped,
            x="RAILROAD",
            y="count",
            color="TYPE",
            barmode="group",
            title="4.2 Incident Types by Railroad",
            labels={
                "RAILROAD": self.aliases.get("RAILROAD", "Operator"),
                "TYPE": self.aliases.get("TYPE", "Incident Type"),
                "count": "Count",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_4_3_operator_higher_lower_specific_incidents(self) -> go.Figure:
        """
        4.3: Which operator is higher/lower for specific incidents?
        => box: x=RAILROAD, y=ACCDMG
        """
        needed = ["RAILROAD", "ACCDMG"]
        if not all(n in self.df.columns for n in needed):
            return go.Figure()

        fig = px.box(
            self.df,
            x="RAILROAD",
            y="ACCDMG",
            title="4.3 Damage by Railroad",
            labels={
                "RAILROAD": self.aliases.get("RAILROAD", "Operator"),
                "ACCDMG": self.aliases.get("ACCDMG", "Damage Cost"),
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    # --------------- (5) High-Impact Incidents ---------------
    def plot_5_1_primary_secondary_causes(self) -> go.Figure:
        """
        5.1: Primary & secondary causes of high-impact incidents
        => group by (CAUSE, CAUSE2), only include outliers
        """
        needed = ["CAUSE", "CAUSE2"]
        if not all(n in self.df.columns for n in needed):
            return go.Figure()

        # Define the outlier filtering criteria (example: using IQR for numeric columns)
        if 'count' in self.df.columns:
            Q1 = self.df['count'].quantile(0.25)
            Q3 = self.df['count'].quantile(0.75)
            IQR = Q3 - Q1
            outlier_condition = (self.df['count'] < (Q1 - 1.5 * IQR)) | (self.df['count'] > (Q3 + 1.5 * IQR))
            filtered_df = self.df[outlier_condition]
        else:
            filtered_df = self.df  # Default: no outlier detection if "count" is not available

        # Group by "CAUSE" and "CAUSE2" on filtered data
        grouped = filtered_df.groupby(["CAUSE", "CAUSE2"]).size().reset_index(name="count")

        # Create the plot
        fig = px.bar(
            grouped,
            x="CAUSE",
            y="count",
            color="CAUSE2",
            barmode="group",
            title="5.1 Primary vs. Secondary Causes (Outliers Only)",
            labels={
                "CAUSE": "Primary Cause",
                "CAUSE2": "Secondary Cause",
                "count": "Count",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_5_2_common_circumstances_severe_incidents(self) -> go.Figure:
        """
        5.2: Common circumstances in severe incidents?
        => define severe as ACCDMG>100000 (arbitrary), then do a pie of TYPE
        """
        if "ACCDMG" not in self.df.columns or "TYPE" not in self.df.columns:
            return go.Figure()

        severe = self.df[self.df["ACCDMG"] > 100000]
        if severe.empty:
            # fallback if no severe found
            severe = self.df
        counts = severe["TYPE"].value_counts().nlargest(5).reset_index()
        counts.columns = ["TYPE", "count"]
        fig = px.pie(
            counts,
            names="TYPE",
            values="count",
            title="5.2 Common Incident Types in Severe Incidents",
            labels={
                "TYPE": self.aliases.get("TYPE", "Incident Type"),
                "count": "Count",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_5_3_preventable_factors(self) -> go.Figure:
        """
        5.3: Preventable factors in high-impact incidents?
        => if we have 'ACCAUSE' column, bar of top 10
        """
        if "ACCAUSE" not in self.df.columns:
            return go.Figure()

        factor_counts = self.df["ACCAUSE"].value_counts().nlargest(10).reset_index()
        factor_counts.columns = ["ACCAUSE", "count"]
        fig = px.bar(
            factor_counts,
            x="ACCAUSE",
            y="count",
            title="5.3 Preventable Factors in High-Impact Incidents",
            labels={
                "ACCAUSE": "Accident Cause",
                "count": "Count",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    # --------------- (6) Summarizing Incident Characteristics ---------------
    def plot_6_1_most_common_incident_types(self) -> go.Figure:
        """
        6.1: Most common types of railroad incidents => TYPE (top 10)
        """
        if "TYPE" not in self.df.columns:
            return go.Figure()

        type_counts = self.df["TYPE"].value_counts().nlargest(10).reset_index()
        type_counts.columns = ["TYPE", "count"]
        fig = px.bar(
            type_counts,
            x="TYPE",
            y="count",
            title="6.1 Most Common Incident Types",
            labels={
                "TYPE": self.aliases.get("TYPE", "Incident Type"),
                "count": "Count",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_6_2_most_frequent_primary_causes(self) -> go.Figure:
        """
        6.2: Most frequently cited primary causes => CAUSE
        """
        if "CAUSE" not in self.df.columns:
            return go.Figure()

        cause_counts = self.df["CAUSE"].value_counts().nlargest(10).reset_index()
        cause_counts.columns = ["CAUSE", "count"]
        fig = px.bar(
            cause_counts,
            x="CAUSE",
            y="count",
            title="6.2 Most Frequently Cited Primary Causes",
            labels={
                "CAUSE": "Primary Cause",
                "count": "Count",
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig

    def plot_6_3_avg_damage_by_incident_types(self) -> go.Figure:
        """
        6.3: Avg damage cost among different incident types => violin plot x=TYPE, y=ACCDMG
        """
        needed = ["TYPE", "ACCDMG"]
        if not all(n in self.df.columns for n in needed):
            return go.Figure()

        fig = px.violin(
            self.df,
            x="TYPE",
            y="ACCDMG",
            box=True,  # Adds a box plot inside the violin for additional information
            points="all",  # Adds all data points
            title="6.3 Avg Damage by Incident Type",
            labels={
                "TYPE": self.aliases.get("TYPE", "Incident Type"),
                "ACCDMG": self.aliases.get("ACCDMG", "Damage Cost"),
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white",
            width=1200,  # Adjust width to fit the available space
            height=600  # Adjust height to fit the available space
        )
        return fig

