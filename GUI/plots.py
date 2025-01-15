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

#
# If you want a TreemapPlot, you can add it similarly:
#
# class TreemapPlot:
#     ...
