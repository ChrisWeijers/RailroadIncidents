import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List
import geopandas as gpd

# If you have a config for the US polygon:
try:
    from GUI.config import US_POLYGON  # or wherever your polygon/geo is defined
except ImportError:
    # If you don't have US_POLYGON, comment this out or provide your own polygon
    US_POLYGON = None


class Map:
    """
    A class to create and manage an interactive choropleth map using Plotly and Mapbox.
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
            mapbox=dict(style="carto-darkmatter", center=center, zoom=zoom),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            paper_bgcolor='darkgrey',
            font=dict(color='white', size=12),
            showlegend=False,
            transition={'duration': 500, 'easing': 'elastic-in-out'},
        )
        return self.fig

    def add_points(self, df_state: pd.DataFrame, name: str) -> None:
        """
        Adds points/density to the map (e.g., for incidences).
        """
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
                )
            )

    def highlight_state(self, hovered_state: str, trace_name: str) -> None:
        """
        Adds a highlight boundary for a hovered or clicked state.
        """
        hovered_geometry = None
        for feature in self.us_states['features']:
            if feature['properties']['name'] == hovered_state:
                hovered_geometry = feature['geometry']
                break

        if not hovered_geometry:
            return

        geom_type = hovered_geometry['type']
        coords_list = []
        if geom_type == 'Polygon':
            coords_list = [hovered_geometry['coordinates']]
        elif geom_type == 'MultiPolygon':
            coords_list = hovered_geometry['coordinates']

        for coords_set in coords_list:
            # coords_set might be a list of rings
            for coords in coords_set:
                self.fig.add_trace(
                    go.Scattermapbox(
                        lon=[pt[0] for pt in coords],
                        lat=[pt[1] for pt in coords],
                        mode='lines',
                        line=dict(color='lightgrey', width=1),
                        hoverinfo='skip',
                        opacity=0.6,
                        name=trace_name,
                    )
                )

        self.fig.update_layout(
            hovermode='closest',
            transition={'duration': 500, 'easing': 'elastic-in-out'}
        )


class BarChart:
    """
    Simple horizontal bar chart for the top-level state_count usage,
    though you can adapt it for other horizontal bar needs.
    """

    def __init__(self, state_count: pd.DataFrame) -> None:
        self.state_count = state_count
        self.bar = None

    def create_barchart(self) -> go.Figure:
        self.bar = px.bar(
            self.state_count,
            x='crash_count',
            y='state_name',
            text='state_name',
            color_discrete_sequence=['white'],
            hover_data={'crash_count': True},
            orientation='h'
        )

        self.bar.update_traces(
            textfont=dict(color="white"),
            textposition='outside',
            hovertemplate="<b>%{text}</b><br>Crashes: %{x:,}<extra></extra>",
            hoverlabel=dict(
                bgcolor="lightgrey",
                bordercolor="grey",
                font=dict(size=14, color="black", family="Helvetica")
            ),
        )
        self.bar.update_yaxes(visible=False, showticklabels=False)
        self.bar.update_xaxes(visible=False, showticklabels=False)

        self.bar.update_layout(
            uirevision=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
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
            title="1.1 Total Incidents Over Time",
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
        6.3: Avg damage cost among different incident types => box x=TYPE, y=ACCDMG
        """
        needed = ["TYPE", "ACCDMG"]
        if not all(n in self.df.columns for n in needed):
            return go.Figure()

        fig = px.box(
            self.df,
            x="TYPE",
            y="ACCDMG",
            title="6.3 Avg Damage by Incident Type",
            labels={
                "TYPE": self.aliases.get("TYPE", "Incident Type"),
                "ACCDMG": self.aliases.get("ACCDMG", "Damage Cost"),
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig
