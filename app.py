from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
from GUI.data import get_data
from GUI.plots import Map, BarChart

df, states_center, state_count, us_states = get_data()

app = Dash(__name__)
app.title = 'Railroad Dashboard'

# External stylesheet (assuming you saved the provided CSS as 'assets/style.css')
# Dash automatically serves files placed in the 'assets' directory.
external_stylesheets = [
    # If you placed the CSS in the assets folder, Dash will load it automatically.
    # If you placed it elsewhere, provide the URL or static path here.
]

app.layout = html.Div(
    className='main-container',
    children=[
        # Sidebar: now we control it using inline style
        html.Div(
            id="popup-sidebar",
            className="popup-sidebar",
            style={'display': 'none'},  # start hidden
            children=[
                html.Div(
                    id="state-popup",
                    className="popup-content",
                    children=[
                        html.H3(id="popup-title"),
                        html.Div(id="popup-details"),
                        html.Button("Close", id="close-popup"),
                    ],
                )
            ]
        ),
        # Main content area
        html.Div(
            className='content-area',
            children=[
                dcc.Store(id='selected-state', storage_type='memory'),
                dcc.Store(id='manual-zoom', storage_type='memory',
                          data={'zoom': 3, 'center': {'lat': 39.8282, 'lon': -98.5795}}),
                html.H1("Interactive Railroad Accidents by State", style={"textAlign": "center"}),
                dcc.Graph(
                    id='crash-map',
                    className='graph-container',
                    config={
                        'scrollZoom': True,
                        'doubleClick': 'reset',
                        'displayModeBar': True,
                    },
                ),
                dcc.Graph(
                    id='barchart',
                    className='graph-container'
                ),
            ]
        )
    ]
)


@app.callback(
    [
        Output('popup-sidebar', 'style'),
        Output('manual-zoom', 'data'),
        Output('selected-state', 'data'),
        Output('popup-title', 'children'),
        Output('popup-details', 'children')
    ],
    [
        Input('crash-map', 'relayoutData'),
        Input('crash-map', 'clickData'),
        Input('barchart', 'clickData'),
        Input('close-popup', 'n_clicks')
    ],
    [
        State('manual-zoom', 'data'),
        State('selected-state', 'data')
    ]
)
def handle_map_interactions(relayout_data, map_click, bar_click, close_click, current_zoom_state, current_selected):
    ctx = callback_context
    if not ctx.triggered:
        # No triggers yet
        return {'display': 'none'}, current_zoom_state, current_selected, "", ""

    trigger_id, trigger_prop = ctx.triggered[0]['prop_id'].split('.')

    default_view = {
        'zoom': 3,
        'center': {'lat': 39.8282, 'lon': -98.5795}
    }

    # 1. Handle Closing the Sidebar
    if trigger_id == 'close-popup' and close_click:
        # Reset selected state and hide sidebar
        return {'display': 'none'}, default_view, None, "", ""

    # 2. Identify if a New State Was Clicked
    clicked_state = None
    if trigger_id == 'crash-map' and map_click:
        point_data = map_click['points'][0]
        clicked_state = point_data.get('customdata') or \
                        (point_data.get('text', '').split('<br>')[0] if point_data.get('text') else None)
    elif trigger_id == 'barchart' and bar_click:
        clicked_state = bar_click['points'][0].get('label') or bar_click['points'][0].get('x')

    # Update selected_state if a new state was clicked
    if clicked_state:
        current_selected = clicked_state

    # 3. Update Manual Zoom/Center on Map Movement
    if trigger_id == 'crash-map' and relayout_data:
        new_zoom = relayout_data.get('mapbox.zoom', current_zoom_state['zoom'])
        new_center = {
            'lat': relayout_data.get('mapbox.center', current_zoom_state['center'])['lat']
            if 'mapbox.center' in relayout_data else current_zoom_state['center']['lat'],
            'lon': relayout_data.get('mapbox.center', current_zoom_state['center'])['lon']
            if 'mapbox.center' in relayout_data else current_zoom_state['center']['lon']
        }
        current_zoom_state = {'zoom': new_zoom, 'center': new_center}

    # 4. Decide Whether to Show the Sidebar
    # Only show the sidebar if:
    # - We have a currently selected state (current_selected not None)
    # - The trigger event was actually a click on a state (map_click or bar_click)
    # If the trigger is relayoutData (map movement), do not show the sidebar.
    if current_selected and (trigger_id == 'crash-map' or trigger_id == 'barchart') and clicked_state is not None:
        if current_selected in state_count['state_name'].values:
            crash_count = state_count[state_count['state_name'] == current_selected]['crash_count'].values[0]
            popup_title = current_selected
            popup_details = html.Div([html.P(f"Total Crashes: {crash_count}")])
        else:
            popup_title = current_selected
            popup_details = html.Div([html.P("No data available")])
        sidebar_style = {'display': 'block'}
    else:
        # If no new state clicked or trigger is not a click event, keep sidebar hidden
        sidebar_style = {'display': 'none'}
        popup_title = ""
        popup_details = ""

    return sidebar_style, current_zoom_state, current_selected, popup_title, popup_details




@app.callback(
    [Output('crash-map', 'figure'),
     Output('barchart', 'figure')],
    [Input('crash-map', 'hoverData'),
     Input('barchart', 'hoverData'),
     Input('selected-state', 'data'),
     Input('crash-map', 'relayoutData'),
     Input('manual-zoom', 'data')]
)
def update_map(hover_map, hover_bar, selected_state, relayout, manual_zoom):
    bar = BarChart(state_count).create_barchart()
    us = Map(df, us_states, state_count, manual_zoom)
    fig = us.plot_map()

    # Handle hover interactions (optional)
    hovered_state = None
    if hover_map:
        hovered_point = hover_map['points'][0]
        hovered_state = hovered_point.get('customdata') or hovered_point.get('text', '').split('<br>')[0]
    elif hover_bar:
        hovered_point = hover_bar['points'][0]
        hovered_state = hovered_point.get('label') or hovered_point.get('name')

    if hovered_state:
        us.highlight_state(hovered_state, 'hoverstate')

    # Preserve selected state highlight and points
    if selected_state:
        df_state = df[df['state_name'] == selected_state]
        us.highlight_state(selected_state, 'clickstate')
        us.add_points(df_state, 'clickstate')

    # Add points if zoomed in sufficiently
    if relayout and 'mapbox.zoom' in relayout:
        if relayout['mapbox.zoom'] >= 4.5:
            us.add_points(df, 'all_points')

    return fig, bar

if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_ui=False)
