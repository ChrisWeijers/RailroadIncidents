import plotly.express as px
import plotly.graph_objects as go


class Map:
    def __init__(self, df, us_states, state_count, manual_zoom):
        self.df = df
        self.us_states = us_states
        self.state_count = state_count
        self.manual_zoom = manual_zoom

    def plot_map(self):
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
            height=900,
            paper_bgcolor='darkgrey',
            font=dict(color='white', size=12),
            showlegend=False,
            transition={'duration': 500, 'easing': 'elastic-in-out'}
        )
        return self.fig

    def add_points(self, df_state, name):
        """
        Adds incident points to the map for the selected state.
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

    def highlight_state(self, hovered_state, trace_name):
        """
        Adds a highlight trace for a hovered state to the figure.
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
    def __init__(self, state_count):
        self.state_count = state_count

    def create_barchart(self):
        # Create bar chart
        self.bar = px.bar(self.state_count,
                          x='state_name',
                          y='crash_count',
                          title='States by Crash Count',
                          labels={'state_name': 'State', 'crash_count': 'Crashes'},
                          hover_data={'crash_count': True},
                          color_discrete_sequence=['white'])

        self.bar.update_traces(
            hovertemplate="<b>%{x}</b><br>Crashes: %{y:,}<extra></extra>",
            hoverlabel=dict(
                bgcolor="lightgrey",
                bordercolor="grey",
                font=dict(size=14, color="black", family="Helvetica")
            )
        )

        self.bar.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font_color='grey',
            title_font_color='grey'
        )

        return self.bar
