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
        className='main-container',
        children=[
            html.Div(
                id="popup-sidebar",
                className="popup-sidebar",
                children=[
                    html.Div(
                        id='barchart-button',
                        className='arrow-button',
                        title='Switch to filters',
                        children=[html.Div(className='arrow-down')],
                        style={'display': 'block'}
                    ),
                    dcc.Graph(
                        id='barchart',
                        className='barchart',
                        config={'displayModeBar': False},
                        style={'display': 'block'},
                    ),

                    html.Div(
                        id="state-popup",
                        className="popup-content",
                        style={'display': 'none'},
                        children=[
                            html.Div(
                                className='button-container',
                                style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'gap': '10px',
                                    'marginBottom': '10px'
                                },
                                children=[
                                    html.Div(
                                        id='sidebar-button',
                                        className='arrow-button',
                                        title='Switch to barchart',
                                        children=[html.Div(className='arrow')]
                                    ),
                                    html.Button(
                                        id='clear-selection-button',
                                        className='clear-button',
                                        title='Clear Selection',
                                        style={'display': 'none'}
                                    ),
                                ]
                            ),

                            html.H3(id="popup-title"),
                            html.Div(id="popup-details"),

                            # Year Range Slider
                            html.Label("Select Year Range"),
                            dcc.RangeSlider(
                                id='year-slider',
                                min=config['year_min'],
                                max=config['year_max'],
                                value=[config['year_min'], config['year_max']],
                                marks={str(y): str(y) for y in range(config['year_min'], config['year_max'] + 1, 4)},
                                step=1
                            ),

                            # Month Slider
                            html.Label("Select Month"),
                            dcc.RangeSlider(
                                id='month-slider',
                                min=config['month_min'],
                                max=config['month_max'],
                                value=[config['month_min'], config['month_max']],
                                marks={str(m): str(m) for m in range(config['month_min'], config['month_max'] + 1)},
                                step=1
                            ),

                            # Damage Slider
                            html.Label("Select Damage Range"),
                            dcc.RangeSlider(
                                id='damage-slider',
                                min=config['damage_min'],
                                max=config['damage_max'],
                                value=[config['damage_min'], config['damage_max']],
                                marks={
                                    str(int(d)): str(int(d)) for d in [
                                        config['damage_min'],
                                        (config['damage_min'] + config['damage_max']) // 2,
                                        config['damage_max']
                                    ]
                                },
                                step=(config['damage_max'] - config['damage_min']) / 100.0 if config['damage_max'] > config['damage_min'] else 1
                            ),

                            # Injuries Slider
                            html.Label("Select Injuries Range"),
                            dcc.RangeSlider(
                                id='injuries-slider',
                                min=config['injuries_min'],
                                max=config['injuries_max'],
                                value=[config['injuries_min'], config['injuries_max']],
                                marks={
                                    str(int(i)): str(int(i)) for i in [
                                        config['injuries_min'],
                                        (config['injuries_min'] + config['injuries_max']) // 2,
                                        config['injuries_max']
                                    ]
                                },
                                step=1
                            ),

                            # Speed Slider
                            html.Label("Select Speed Range"),
                            dcc.RangeSlider(
                                id='speed-slider',
                                min=config['speed_min'],
                                max=config['speed_max'],
                                value=[config['speed_min'], config['speed_max']],
                                marks={
                                    str(int(s)): str(int(s)) for s in [
                                        config['speed_min'],
                                        (config['speed_min'] + config['speed_max']) // 2,
                                        config['speed_max']
                                    ]
                                },
                                step=1
                            ),
                        ],
                    )
                ]
            ),

            html.Div(
                className='content-area',
                children=[
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