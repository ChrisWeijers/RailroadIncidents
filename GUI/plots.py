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
                go.Scattermapbox(
                    lat=df_state['Latitude'],
                    lon=df_state['Longitud'],
                    mode='markers',
                    marker=dict(
                        size=6,
                        color='darkred',
                        opacity=0.5
                    ),
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
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )

        return self.bar


class LineChart:
    """
    A class to create and manage a line chart showing the number of incidents per year using Plotly.

    Attributes:
        state_count (pd.DataFrame): DataFrame containing incident data with at least 'year' and 'crash_count' columns.
    """

    def __init__(self, state_count: pd.DataFrame) -> None:
        """
        Initializes the LineChart with the provided DataFrame.

        Args:
            state_count (pd.DataFrame): DataFrame containing incident data with at least 'year' and 'crash_count' columns.
        """
        self.state_count = state_count

    def create_linechart(self) -> go.Figure:
        """
        Creates a line chart showing the number of incidents per year.

        Returns:
            go.Figure: A Plotly Figure object representing the line chart.
        """
        # Aggregate crash counts per year
        df_yearly = self.state_count.groupby('year')['crash_count'].sum().reset_index()

        # Create the line chart
        fig = px.line(
            df_yearly,
            x='year',
            y='crash_count',
            title='Incidents per Year',
            labels={'year': 'Year', 'crash_count': 'Number of Crashes'},
            markers=True,  # Adds markers to each data point
            color_discrete_sequence=['#1f77b4']  # You can choose any color you prefer
        )

        # Update hover information
        fig.update_traces(
            hovertemplate="<b>Year %{x}</b><br>Crashes: %{y:,}<extra></extra>"
        )

        # Update layout for consistent styling
        fig.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
            paper_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
            font=dict(color='grey', size=12),
            title_font=dict(color='grey'),
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgrey'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgrey'
            ),
            hovermode='x unified'  # Makes hover effects consistent
        )

        # Optional: Add transition for smooth updates
        fig.update_layout(transition={'duration': 500, 'easing': 'elastic-in-out'})

        return fig
