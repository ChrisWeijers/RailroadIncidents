import dash
from dash import Output, Input, State, callback
from dash import callback_context
from GUI.plots import Map, BarChart
from dash import html
import pandas as pd
from typing import List, Dict, Any

def setup_callbacks(app, df: pd.DataFrame, state_count: pd.DataFrame, us_states: Dict[str, Any], df_map: pd.DataFrame) -> None:
    """
    Sets up all the callback functions for the Dash application.

    This function defines callbacks for handling user interactions with the map,
    bar chart, sidebar, and various controls (top portion),
    AND the new bottom portion (attributes + visualizations).
    """

    # ------------------------- TOP CALLBACKS (UNCHANGED) ------------------------

    @app.callback(
        [Output('manual-zoom', 'data')],
        [Input('crash-map', 'relayoutData')],
        [State('manual-zoom', 'data')]
    )
    def handle_layout_changes(relayout_data: Dict[str, Any], current_zoom_state: Dict[str, Any]):
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        if trigger_id == 'crash-map' and relayout_data:
            new_zoom = relayout_data.get('mapbox.zoom', current_zoom_state.get('zoom', 3))
            new_center = {
                'lat': relayout_data.get('mapbox.center', {}).get('lat', current_zoom_state.get('center', {}).get('lat', 37.8)),
                'lon': relayout_data.get('mapbox.center', {}).get('lon', current_zoom_state.get('center', {}).get('lon', -96))
            }
            current_zoom_state = {'zoom': new_zoom, 'center': new_center}

        return [current_zoom_state]

    @app.callback(
        [Output('states-select', 'value')],
        [Input('crash-map', 'clickData'),
         Input('barchart', 'clickData')],
        [State('selected-state', 'data')]
    )
    def handle_selection(map_click, bar_click, current_selected):
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        selected_state = []
        if trigger_id == 'crash-map' and map_click:
            point_data = map_click['points'][0]
            selected_state = [point_data.get('customdata') or point_data.get('text', '').split('<br>')[0]]
        elif trigger_id == 'barchart' and bar_click:
            selected_state = [bar_click['points'][0].get('label') or bar_click['points'][0].get('x')]

        # If a state is clicked while 'all' is selected, deselect 'all'
        if selected_state and current_selected and 'all' in current_selected:
            current_selected.remove('all')

        return selected_state

    @app.callback(
        Output('hovered-state', 'data'),
        [Input('crash-map', 'hoverData'),
         Input('barchart', 'hoverData')]
    )
    def handle_hover(map_hover, bar_hover):
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        hovered_state = str()
        if trigger_id == 'crash-map' and map_hover:
            point_data = map_hover['points'][0]
            hovered_state = point_data.get('customdata') or point_data.get('text', '').split('<br>')[0]
        elif trigger_id == 'barchart' and bar_hover:
            hovered_state = bar_hover['points'][0].get('label') or bar_hover['points'][0].get('x')

        return hovered_state

    @app.callback(
        [Output('crash-map', 'figure'),
         Output('barchart', 'figure')],
        [Input('states-select', 'value'),
         Input('hovered-state', 'data'),
         Input('manual-zoom', 'data')]
    )
    def update_map(selected_state, hovered_state, manual_zoom):
        """
        EXACT logic from your original top chart code:
          - Builds bar chart
          - Builds map
          - Highlights hovered states
          - Adds points for selected states
        """
        from GUI.plots import Map, BarChart

        bar = BarChart(state_count).create_barchart()
        us_map = Map(df, us_states, state_count, manual_zoom)
        fig_map = us_map.plot_map()

        if hovered_state:
            us_map.highlight_state(hovered_state, 'hoverstate')

        if selected_state:
            if 'all' in selected_state:
                us_map.add_points(df, 'clickstate')
                bar = BarChart(state_count).create_barchart()
            else:
                us_map.highlight_state(selected_state, 'clickstate')

            if not isinstance(selected_state, list):
                selected_state = [selected_state]
            df_filtered = df_map[df_map['state_name'].isin(selected_state)]
            us_map.add_points(df_filtered, 'clickstate')

            if len(selected_state) > 1:
                state_count_filtered = state_count[state_count['state_name'].isin(selected_state)]
                bar = BarChart(state_count_filtered).create_barchart()

        return fig_map, bar

    # --------------------- NEW BOTTOM CHARTS CALLBACK ---------------------

    @app.callback(
        [Output('plot-left', 'figure'),
         Output('plot-right', 'figure'),
         Output('plot-left', 'style'),
         Output('plot-right', 'style')
         ],
        [
            Input('states-select', 'value'),
            Input('attributes-dropdown', 'value'),
            Input('viz-dropdown', 'value')
        ]
    )
    def update_bottom_charts(selected_states, selected_attrs, selected_viz):
        """
        Renders up to two charts in the bottom placeholders (plot-left, plot-right),
        based on user selections:
          - states-select (which states),
          - attributes-dropdown (which columns),
          - viz-dropdown (which chart types).
        """
        import plotly.express as px

        # 1) If user hasn't selected any visualization, return empty
        if not selected_viz:
            return {}, {}

        # 2) Filter by selected states (if 'all' not in the list)
        if selected_states and ('all' not in selected_states):
            dff = df[df['state_name'].isin(selected_states)]
        else:
            dff = df.copy()

        # 3) Decide how to handle multiple attributes
        #    If user picks 2, we can do x = first, y = second for scatter
        x_attr = selected_attrs[0] if selected_attrs else None
        y_attr = selected_attrs[1] if len(selected_attrs) > 1 else None

        # A small helper function to build a single figure
        def build_figure(vtype):
            if not vtype:
                return {}

            # SCATTER
            if vtype == 'scatter':
                if x_attr and y_attr:
                    fig = px.scatter(
                        dff,
                        x=x_attr,
                        y=y_attr,
                        color='state_name',
                        title=f"Scatter: {x_attr} vs. {y_attr}"
                    )
                else:
                    fig = {}
            # BAR
            elif vtype == 'bar':
                # If we have an x_attr, let's group by state and do average
                if x_attr:
                    grouped = dff.groupby('state_name', as_index=False)[x_attr].mean()
                    fig = px.bar(
                        grouped,
                        x='state_name',
                        y=x_attr,
                        title=f"Bar: avg({x_attr}) by State"
                    )
                else:
                    fig = {}
            # BOX
            elif vtype == 'box':
                if x_attr:
                    fig = px.box(
                        dff,
                        x='state_name',
                        y=x_attr,
                        title=f"Box Plot of {x_attr} by State"
                    )
                else:
                    fig = {}
            else:
                fig = {}

            return fig

        # 4) If user picked only one chart type, show it on the left
        #    If user picked 2 or more, show the first on the left, second on the right
        if len(selected_viz) == 1:
            left_fig = build_figure(selected_viz[0])
            right_fig = {}
        else:
            left_fig = build_figure(selected_viz[0])
            right_fig = build_figure(selected_viz[1]) if len(selected_viz) > 1 else {}

        return left_fig, right_fig
