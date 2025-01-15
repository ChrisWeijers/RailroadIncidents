import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List
import geopandas as gpd
from GUI.config import US_POLYGON  # Adjust if your config file is located elsewhere

class Map:
    """
    A class to create and manage an interactive choropleth map using Plotly and Mapbox.
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

    def plot_map(self) -> go.Figure:
        """
        Generates a choropleth map of the United States, showing crash counts by state.
        """
        self.fig = go.Figure()

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
                    f"{state}<br>Crashes: {count:,}"
                    for state, count in zip(
                        self.state_count['state_name'],
                        self.state_count['crash_count']
                    )
                ],
                hovertemplate="<b>%{text}</b><extra></extra>",
                showscale=False,
                name='States',
            )
        )

        # Use manual_zoom for map center and zoom
        center = (
            self.manual_zoom["center"]
            if self.manual_zoom
            else {"lat": 39.8282, "lon": -98.5795}
        )
        zoom = self.manual_zoom["zoom"] if self.manual_zoom else 3

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
        Adds filtered incident points to the map as a density layer.
        """
        if df_state is not None and not df_state.empty:
            df_state = df_state.dropna(subset=['Latitude', 'Longitud'])

            # Convert DataFrame to GeoDataFrame
            gdf = gpd.GeoDataFrame(
                df_state,
                geometry=gpd.points_from_xy(df_state['Longitud'], df_state['Latitude'])
            )
            # Filter points within the U.S. polygon
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
        Adds a highlight trace for a hovered (or clicked) state boundary on the map.
        """
        hovered_geometry = None
        for feature in self.us_states['features']:
            if feature['properties']['name'] == hovered_state:
                hovered_geometry = feature['geometry']
                break

        if hovered_geometry and hovered_geometry['type'] == 'Polygon':
            for coords in hovered_geometry['coordinates']:
                self.fig.add_trace(
                    go.Scattermapbox(
                        lon=[point[0] for point in coords],
                        lat=[point[1] for point in coords],
                        mode='lines',
                        line=dict(color='lightgrey', width=1),
                        hoverinfo='skip',
                        opacity=0.6,
                        name=trace_name,
                    )
                )
        elif hovered_geometry and hovered_geometry['type'] == 'MultiPolygon':
            for polygon in hovered_geometry['coordinates']:
                for coords in polygon:
                    self.fig.add_trace(
                        go.Scattermapbox(
                            lon=[point[0] for point in coords],
                            lat=[point[1] for point in coords],
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
    A class to create and manage a horizontal bar chart showing crash counts per state.
    """

    def __init__(self, state_count: pd.DataFrame) -> None:
        self.bar = None
        self.state_count = state_count

    def create_barchart(self) -> go.Figure:
        """
        Generates a horizontal bar chart showing the crash counts for each state.
        """
        self.bar = px.bar(
            self.state_count,
            x='crash_count',
            y='state_name',
            text='state_name',
            hover_data={'crash_count': True},
            color_discrete_sequence=['white'],
            orientation='h'
        )

        self.bar.update_yaxes(visible=False, showticklabels=False)
        self.bar.update_xaxes(visible=False, showticklabels=False)

        self.bar.update_traces(
            textfont=dict(color="white"),
            textposition='outside',
            hoverinfo='text',
            hovertemplate="<b>%{text}</b><br>Crashes: %{x:,}<extra></extra>",
            hoverlabel=dict(
                bgcolor="lightgrey",
                bordercolor="grey",
                font=dict(size=14, color="black", family="Helvetica")
            ),
        )

        self.bar.update_layout(
            uirevision=True,
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )

        return self.bar


class LineChart:
    """
    A class to create a line chart showing incidents over time.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    def create(self, selected_states: List[str] = None) -> go.Figure:
        """
        Creates a line chart showing incidents over time, with optional state filtering.
        """
        plot_df = self.df
        if selected_states:
            plot_df = plot_df[plot_df['state_name'].isin(selected_states)]

        # Example grouping by year & month:
        time_series = (
            plot_df.groupby(['year', 'month'])
            .size()
            .reset_index(name='crash_count')
        )

        # Create a datetime column
        time_series['date'] = pd.to_datetime(
            time_series['year'].astype(str)
            + '-'
            + time_series['month'].astype(str).str.zfill(2)
            + '-01'
        )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=time_series['date'],
                y=time_series['crash_count'],
                mode='lines+markers',
                line=dict(color='white', width=2),
                marker=dict(size=6, color='white', line=dict(color='darkgrey', width=1)),
                hovertemplate="<b>%{x|%B %Y}</b><br>Crashes: %{y:,}<extra></extra>",
            )
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            margin=dict(l=40, r=20, t=40, b=20),
            showlegend=False,
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat='%b %Y',
                tickangle=-45,
                tickfont=dict(size=10),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat=',d',
            ),
            hovermode='x unified',
            transition={'duration': 500, 'easing': 'elastic-in-out'},
        )
        return fig


class PieChart:
    """
    A class to create a pie (or donut) chart showing incident distributions by a category.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    def create(self, category: str = 'state_name', selected_states: List[str] = None, top_n: int = 10) -> go.Figure:
        plot_df = self.df
        if selected_states:
            plot_df = plot_df[plot_df['state_name'].isin(selected_states)]

        category_counts = (
            plot_df[category]
            .value_counts()
            .nlargest(top_n)
            .reset_index()
        )
        category_counts.columns = ['category', 'count']

        fig = go.Figure()
        fig.add_trace(
            go.Pie(
                labels=category_counts['category'],
                values=category_counts['count'],
                hole=0.4,  # donut
                marker=dict(
                    colors=['white', 'lightgrey', 'darkgrey', 'grey'] * 3,
                    line=dict(color='black', width=1),
                ),
                textfont=dict(color='black'),
                hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>Percentage: %{percent:.1%}<extra></extra>",
            )
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=True,
            legend=dict(font=dict(color='white'), bgcolor='rgba(0,0,0,0)'),
            transition={'duration': 500, 'easing': 'elastic-in-out'},
        )
        fig.update_traces(textfont=dict(color="white"))
        return fig


class ScatterPlot:
    """
    A generic scatter plot class with optional size or trendline.
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame) -> None:
        self.aliases = aliases
        self.df = df

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
            labels={x_attr: self.aliases.get(x_attr, x_attr),
                    y_attr: self.aliases.get(y_attr, y_attr)}
        )
        fig.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font_color="white"
        )
        return fig

    def create_with_size(self, x_attr: str, y_attr: str, size_attr: str, states: List[str] = None) -> go.Figure:
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
                f"{self.aliases.get(y_attr, y_attr)} (Size = {self.aliases.get(size_attr, size_attr)})"
            ),
            labels={
                x_attr: self.aliases.get(x_attr, x_attr),
                y_attr: self.aliases.get(y_attr, y_attr),
                size_attr: self.aliases.get(size_attr, size_attr),
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font_color="white"
        )
        return fig

    def create_with_trendline(self, x_attr: str, y_attr: str, trendline: str = "ols", states: List[str] = None) -> go.Figure:
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
                f"Scatter with Trendline: {self.aliases.get(x_attr, x_attr)} vs. "
                f"{self.aliases.get(y_attr, y_attr)}"
            ),
            labels={
                x_attr: self.aliases.get(x_attr, x_attr),
                y_attr: self.aliases.get(y_attr, y_attr),
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font_color="white"
        )
        return fig


class GroupedBarChart:
    """
    A class to create grouped bar charts.
    Useful for comparisons across multiple categories (barmode='group').
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame) -> None:
        self.aliases = aliases
        self.df = df

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

        if group_attr and group_attr in dff.columns:
            fig = px.bar(
                dff,
                x=x_attr,
                y=y_attr,
                color=group_attr,
                barmode='group',
                title=(
                    f"Grouped Bar: {self.aliases.get(y_attr, y_attr)} by "
                    f"{self.aliases.get(x_attr, x_attr)} & {self.aliases.get(group_attr, group_attr)}"
                ),
                labels={
                    x_attr: self.aliases.get(x_attr, x_attr),
                    y_attr: self.aliases.get(y_attr, y_attr),
                    group_attr: self.aliases.get(group_attr, group_attr),
                },
            )
        else:
            # fallback to a simple bar chart
            fig = px.bar(
                dff,
                x=x_attr,
                y=y_attr,
                title=f"Bar: {self.aliases.get(y_attr, y_attr)} by {self.aliases.get(x_attr, x_attr)}",
                labels={
                    x_attr: self.aliases.get(x_attr, x_attr),
                    y_attr: self.aliases.get(y_attr, y_attr),
                },
            )
        fig.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font_color="white"
        )
        return fig


class ClusteredBarChart:
    """
    A class to create clustered bar charts (similar to grouped bar).
    Typically used when we have a "cluster_attr" that forms distinct groups.
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame) -> None:
        self.aliases = aliases
        self.df = df

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
                title=(
                    f"Clustered Bar: {self.aliases.get(y_attr, y_attr)} by "
                    f"{self.aliases.get(x_attr, x_attr)} & {self.aliases.get(cluster_attr, cluster_attr)}"
                ),
                labels={
                    x_attr: self.aliases.get(x_attr, x_attr),
                    y_attr: self.aliases.get(y_attr, y_attr),
                    cluster_attr: self.aliases.get(cluster_attr, cluster_attr),
                },
            )
        else:
            fig = px.bar(
                dff,
                x=x_attr,
                y=y_attr,
                title=(
                    f"Bar: {self.aliases.get(y_attr, y_attr)} by "
                    f"{self.aliases.get(x_attr, x_attr)}"
                ),
                labels={
                    x_attr: self.aliases.get(x_attr, x_attr),
                    y_attr: self.aliases.get(y_attr, y_attr),
                },
            )
        fig.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font_color="white"
        )
        return fig


class BoxPlot:
    """
    A class to create box plots (useful for distribution comparisons).
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame) -> None:
        self.aliases = aliases
        self.df = df

    def create(
        self,
        x_attr: str,
        y_attr: str,
        states: List[str] = None
    ) -> go.Figure:
        dff = self.df
        if states:
            dff = dff[dff['state_name'].isin(states)]

        fig = px.box(
            dff,
            x=x_attr,
            y=y_attr,
            color=x_attr,
            title=(
                f"Box Plot of {self.aliases.get(y_attr, y_attr)} by "
                f"{self.aliases.get(x_attr, x_attr)}"
            ),
            labels={
                x_attr: self.aliases.get(x_attr, x_attr),
                y_attr: self.aliases.get(y_attr, y_attr),
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font_color="white"
        )
        return fig


# -------------------------------------------------------------------
# Example classes for #5 (Stacked Bar, TreeMap, etc.) if you want them
# -------------------------------------------------------------------

class StackedBarChart:
    """
    Example of a stacked bar chart to compare multiple damage categories
    (e.g., total damage, equipment damage, track damage).
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame):
        self.aliases = aliases
        self.df = df

    def create(self, category_col: str, damage_cols: List[str]) -> go.Figure:
        """
        Args:
            category_col (str): The column to place along the x-axis (e.g. 'state_name').
            damage_cols (List[str]): The columns to stack (e.g. ['equipment_damage', 'track_damage', 'other_damage']).
        """
        # You may need to pivot or melt your dataframe so that each damage type is in a row
        # For demonstration, let's do a wide-to-long transform (pd.melt)
        dff = self.df.copy()

        melted = dff.melt(
            id_vars=[category_col],
            value_vars=damage_cols,
            var_name='DamageType',
            value_name='DamageValue'
        )
        fig = px.bar(
            melted,
            x=category_col,
            y='DamageValue',
            color='DamageType',
            barmode='stack',
            title=f"Stacked Damage: {', '.join(damage_cols)} by {category_col}",
            labels={
                category_col: self.aliases.get(category_col, category_col),
                'DamageType': 'Damage Type',
                'DamageValue': 'Damage Value',
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig


class TreemapPlot:
    """
    Example class for a Treemap showing the breakdown of total damage
    into various categories.
    """

    def __init__(self, aliases: Dict[str, str], df: pd.DataFrame):
        self.aliases = aliases
        self.df = df

    def create(self, path_cols: List[str], value_col: str) -> go.Figure:
        """
        Args:
            path_cols (List[str]): Hierarchy of categories (e.g. ['state_name', 'damage_type']).
            value_col (str): Numeric column for sizing (e.g. 'damage_value').
        """
        fig = px.treemap(
            self.df,
            path=path_cols,
            values=value_col,
            title=f"Treemap of {value_col} by {' > '.join(path_cols)}",
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return fig
