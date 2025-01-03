from dash import html, dcc
from typing import Dict, Any
import GUI.config


def create_layout(config: list) -> html.Div:
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
        className='container',
        children=[
            html.Div(
                className='top',
                children=[
                    dcc.Graph(
                        id='barchart',
                        className='left',
                        config={
                            'displayModeBar': False,
                            'scrollZoom': True
                        },
                        style={'display': 'block'},
                    ),
                    dcc.Graph(
                        id='crash-map',
                        className='right',
                        config={
                            'scrollZoom': True,
                            'doubleClick': 'reset',
                            'displayModeBar': False,
                        }
                    ),
                ]
            ),
            html.Div(
                className='bottom',
                children=[
                    html.Div(
                        className='dropdown-container',
                        children=[
                            dcc.DatePickerRange(className='datepicker',
                                start_date=str(GUI.config.year_min), end_date=str(GUI.config.year_max)),
                            dcc.Dropdown(
                                id='states-select',
                                className='dropdown',
                                options=[{'label': 'All States', 'value': 'all'}] + [{'label': state, 'value': state} for state in config],
                                multi=True,
                                placeholder='Select state(s)',
                                value=[]
                            ),
                            dcc.Dropdown(
                                className='dropdown',
                                options=['Attributes'],
                                multi=True,
                                placeholder='Attribute'
                            ),
                            dcc.Dropdown(
                                className='dropdown',
                                options=['Barchart', 'Linechart', 'Piechart', 'etc..'],
                                placeholder='Visualization'
                            )
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Div('plot here'),
                            html.Div('plot here')
                        ],
                        className='content')
                ]
            ),
            dcc.Store(id='hovered-state', storage_type='memory'),
            dcc.Store(id='selected-state', storage_type='memory'),
            dcc.Store(
                id='manual-zoom',
                storage_type='memory',
                data={'zoom': 3, 'center': {'lat': 40.003, 'lon': -102.0517}}
            ),
        ]
    )
