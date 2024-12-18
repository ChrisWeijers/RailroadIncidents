from dash import html, dcc
from typing import Dict, Any

def create_layout(config: Dict[str, Any]) -> html.Div:
    """
    Generates the main layout for the Dash application.

    The layout includes a sidebar with a bar chart, state-specific details,
    and various range sliders for filtering data. It also includes a map
    display area.

    Args:
        config (Dict[str, Any]): A dictionary containing configuration parameters
            for the layout. Expected keys include:
                - 'year_min' (int): Minimum year for the year slider.
                - 'year_max' (int): Maximum year for the year slider.
                - 'month_min' (int): Minimum month for the month slider.
                - 'month_max' (int): Maximum month for the month slider.
                - 'damage_min' (float): Minimum damage value for the damage slider.
                - 'damage_max' (float): Maximum damage value for the damage slider.
                - 'injuries_min' (int): Minimum injury value for the injury slider.
                - 'injuries_max' (int): Maximum injury value for the injury slider.
                - 'speed_min' (float): Minimum speed value for the speed slider.
                - 'speed_max' (float): Maximum speed value for the speed slider.


    Returns:
        html.Div: The main layout as a Dash HTML Div component.
    """
    return html.Div(
        children=[
            html.Div(
                id="popup-sidebar",
                className="popup-sidebar",
                children=[
                    dcc.Graph(
                        id='barchart',
                        className='barchart',
                        config={'displayModeBar': False},
                        style={'display': 'block'},
                    ),
                ]
            ),

            html.Div(
                className='content-area',
                children=[
                    dcc.Store(id='hovered-state', storage_type='memory'),
                    dcc.Store(id='selected-state', storage_type='memory'),
                    dcc.Store(
                        id='manual-zoom',
                        storage_type='memory',
                        data={'zoom': 3, 'center': {'lat': 40.003, 'lon': -102.0517}}
                    ),

                    dcc.Graph(
                        id='crash-map',
                        className='graph-container',
                        config={
                            'scrollZoom': True,
                            'doubleClick': 'reset',
                            'displayModeBar': False,
                        }
                    ),
                ]
            )
        ]
    )