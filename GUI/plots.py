import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List


class Map:
    """
    A class to create and manage an interactive choropleth map using Plotly and Mapbox.

    Attributes:
        df (pd.DataFrame): The main DataFrame containing incident data.
        us_states (Dict): GeoJSON data for US states.
        state_count (pd.DataFrame): DataFrame containing the count of incidents per state.
        manual_zoom (Dict): Dictionary specifying manual zoom level and center for the map.
        fig (go.Figure): The Plotly figure object for the map.
    """

    def __init__(self, df: pd.DataFrame, us_states: Dict[str, Any], state_count: pd.DataFrame,
                 manual_zoom: Dict[str, Any]) -> None:
        """
        Initializes the Map object with necessary data and initial zoom settings.

        Args:
            df (pd.DataFrame): The main DataFrame containing the accident data.
            us_states (Dict[str, Any]): GeoJSON data for the US states.
            state_count (pd.DataFrame): DataFrame containing crash counts per state.
            manual_zoom (Dict[str, Any]): Initial map zoom and center settings.
        """
        self.df = df
        self.us_states = us_states
        self.state_count = state_count
        self.manual_zoom = manual_zoom

    def plot_map(self) -> go.Figure:
        """
        Generates a choropleth map of the United States, showing crash counts by state.

        Returns:
            go.Figure: The Plotly figure object representing the choropleth map.
        """
        self.fig = go.Figure()

        self.fig.add_trace(
            go.Choroplethmapbox(
                geojson=self.us_states,
                locations=self.state_count['state_name'],
                z=self.state_count['crash_count'],
                featureidkey="properties.name",
                colorscale=[[0, 'black'], [1, 'white']],
                marker_opacity=0.25,
                marker_line_width=0.5,
                marker_line_color='lightgrey',
                hoverinfo='text',
                # Store the clean state name in 'customdata' for use in callbacks
                customdata=self.state_count['state_name'],
                text=[f"{state}<br>Crashes: {count:,}" for state, count in
                      zip(self.state_count['state_name'], self.state_count['crash_count'])],
                hovertemplate="<b>%{text}</b><extra></extra>",
                showscale=False,
                name='States'
            )
        )

        # Use manual_zoom for map center and zoom
        center = self.manual_zoom['center'] if self.manual_zoom else {'lat': 39.8282, 'lon': -98.5795}
        zoom = self.manual_zoom['zoom'] if self.manual_zoom else 3

        self.fig.update_layout(
            mapbox=dict(
                style="carto-darkmatter",
                center=center,
                zoom=zoom
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            paper_bgcolor='darkgrey',
            font=dict(color='white', size=12),
            showlegend=False,
            transition={'duration': 500, 'easing': 'elastic-in-out'}
        )
        return self.fig

    def add_points(self, df_state: pd.DataFrame, name: str) -> None:
        """
        Adds incident points to the map for the selected state.

        Args:
            df_state (pd.DataFrame): DataFrame containing accident data for a specific state.
            name (str): The name to assign to the trace.
        """
        if df_state is not None and not df_state.empty:
            self.fig.add_trace(
                go.Densitymapbox(
                    lat=df_state['Latitude'],
                    lon=df_state['Longitud'],
                    radius=3,
                    showscale=False,
                    #colorscale='Blackbody', Possible to change the colorscale if wanted
                    hoverinfo='skip',
                    customdata=df_state['state_name'].tolist(),  # Ensure customdata is set
                    name=name,
                ),
            )

    def highlight_state(self, hovered_state: str, trace_name: str) -> None:
        """
        Adds a highlight trace for a hovered state to the map.

         Args:
            hovered_state (str): Name of the state to highlight.
            trace_name (str): The name to assign to the highlight trace.
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
        self.fig.update_layout(hovermode='closest', transition={'duration': 500, 'easing': 'elastic-in-out'})


class BarChart:
    """
    A class to create and manage a horizontal bar chart using Plotly.

    Attributes:
        state_count (pd.DataFrame): DataFrame containing the count of incidents per state.
        bar (go.Figure): The Plotly figure object for the bar chart.
    """

    def __init__(self, state_count: pd.DataFrame) -> None:
        """
         Initializes the BarChart with state crash count data.

        Args:
            state_count (pd.DataFrame): DataFrame containing crash counts per state,
                with 'state_name' and 'crash_count' columns.
        """
        self.bar = None
        self.state_count = state_count

    def create_barchart(self) -> go.Figure:
        """
        Generates a horizontal bar chart showing the crash counts for each state.

        Returns:
            go.Figure: The Plotly figure object representing the bar chart.
        """
        # Create bar chart
        self.bar = px.bar(self.state_count,
                          x='crash_count',
                          y='state_name',
                          text='state_name',
                          hover_data={'crash_count': True},
                          color_discrete_sequence=['white'],
                          orientation='h')

        self.bar.update_yaxes(visible=False, showticklabels=False)
        self.bar.update_xaxes(visible=False, showticklabels=False,)

        self.bar.update_traces(
            textfont=dict(color="white"),
            textposition='outside',
            hoverinfo='text',
            hovertemplate="<b>%{text}</b><br>Crashes: %{x:,}<extra></extra>",
            hoverlabel=dict(
                bgcolor="lightgrey",
                bordercolor="grey",
                font=dict(size=14, color="black", family="Helvetica")
            )
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
    A class to create and manage a line chart showing incidents over time using Plotly.

    Attributes:
        df (pd.DataFrame): DataFrame containing incident data.
        line (go.Figure): The Plotly figure object for the line chart.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Initializes the LineChart with incident data.

        Args:
            df (pd.DataFrame): DataFrame containing incident data with date/time information.
        """
        self.df = df
        self.line = None

    def create_linechart(self, selected_states: List[str] = None) -> go.Figure:
        """
        Creates a line chart showing incidents over time, with optional state filtering.

        Args:
            selected_states (List[str], optional): List of states to filter data for.

        Returns:
            go.Figure: The Plotly figure object representing the line chart.
        """
        # Filter data if states are selected
        plot_df = self.df
        if selected_states and 'all' not in selected_states:
            plot_df = self.df[self.df['state_name'].isin(selected_states)]

        # Aggregate by year and month
        time_series = (plot_df.groupby(['year', 'month'])
                       .size()
                       .reset_index(name='crash_count'))

        # Create datetime for proper x-axis ordering
        time_series['date'] = pd.to_datetime(
            time_series['year'].astype(str) + '-' +
            time_series['month'].astype(str).str.zfill(2) + '-01'
        )

        self.line = go.Figure()

        # Add the line trace
        self.line.add_trace(
            go.Scatter(
                x=time_series['date'],
                y=time_series['crash_count'],
                mode='lines+markers',
                line=dict(color='white', width=2),
                marker=dict(
                    size=6,
                    color='white',
                    line=dict(color='darkgrey', width=1)
                ),
                hovertemplate=(
                        "<b>%{x|%B %Y}</b><br>" +
                        "Crashes: %{y:,}<extra></extra>"
                )
            )
        )

        # Update layout with your dark theme
        self.line.update_layout(
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
                tickfont=dict(size=10)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat=',d'
            ),
            hovermode='x unified',
            transition={'duration': 500, 'easing': 'elastic-in-out'}
        )

        return self.line


class PieChart:
    """
    A class to create and manage a pie chart showing incident distributions using Plotly.

    Attributes:
        df (pd.DataFrame): DataFrame containing incident data.
        pie (go.Figure): The Plotly figure object for the pie chart.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Initializes the PieChart with incident data.

        Args:
            df (pd.DataFrame): DataFrame containing incident data.
        """
        self.df = df
        self.pie = None

    def create_piechart(self,
                        category: str = 'state_name',
                        selected_states: List[str] = None,
                        top_n: int = 10) -> go.Figure:
        """
        Creates a pie chart showing the distribution of incidents by the specified category.

        Args:
            category (str): Column name to group data by (default: 'state_name')
            selected_states (List[str], optional): List of states to filter data for
            top_n (int): Number of top categories to show (default: 10)

        Returns:
            go.Figure: The Plotly figure object representing the pie chart.
        """
        # Filter data if states are selected
        plot_df = self.df
        if selected_states and 'all' not in selected_states:
            plot_df = self.df[self.df['state_name'].isin(selected_states)]

        # Group by category and get counts
        category_counts = (plot_df[category]
                           .value_counts()
                           .nlargest(top_n)
                           .reset_index())
        category_counts.columns = ['category', 'count']

        # Calculate percentages
        total = category_counts['count'].sum()
        category_counts['percentage'] = (category_counts['count'] / total * 100)

        self.pie = go.Figure()

        # Add pie trace
        self.pie.add_trace(
            go.Pie(
                labels=category_counts['category'],
                values=category_counts['count'],
                hole=0.4,  # Creates a donut chart
                marker=dict(
                    colors=['white', 'lightgrey', 'darkgrey', 'grey'] * 3,
                    line=dict(color='black', width=1)
                ),
                textfont=dict(color='black'),
                hovertemplate=(
                        "<b>%{label}</b><br>" +
                        "Count: %{value:,}<br>" +
                        "Percentage: %{percent:.1%}<extra></extra>"
                )
            )
        )

        # Update layout with your dark theme
        self.pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=True,
            legend=dict(
                font=dict(color='white'),
                bgcolor='rgba(0,0,0,0)'
            ),
            transition={'duration': 500, 'easing': 'elastic-in-out'}
        )

        return self.pie