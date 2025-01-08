from dash import html, dcc
from typing import Dict, Any

def create_layout(config: list, date_min, date_max, attributes) -> html.Div:
    """
    Generates the main layout for the Dash application.

    Top:
      - barchart (left)
      - crash-map (right)

    Bottom:
      - RangeSlider
      - states-select (existing)
      - attributes-dropdown (NEW ID)
      - viz-dropdown (NEW ID)
      - plot-left + plot-right graphs
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
                            dcc.RangeSlider(
                                className='datepicker',
                                min=int(date_min),
                                max=int(date_max),
                                step=1,
                                marks=None,
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": True,
                                    "style": {"fontSize": "10px"}
                                },
                                allowCross=False
                            ),
                            dcc.Dropdown(
                                id='states-select',
                                className='dropdown',
                                options=[{'label': 'All States', 'value': 'all'}]
                                         + [{'label': state, 'value': state} for state in config],
                                multi=True,
                                placeholder='Select state(s)',
                                value=[]
                            ),
                            # -------- NEW: attributes-dropdown (must be label/value pairs) -------
                            dcc.Dropdown(
                                id='attributes-dropdown',
                                className='dropdown',
                                options=[{'label': col, 'value': col} for col in attributes],
                                multi=True,
                                placeholder='Select attribute(s)'
                            ),
                            # -------- NEW: viz-dropdown with chart types --------
                            dcc.Dropdown(
                                id='viz-dropdown',
                                className='dropdown',
                                options=[
                                    {'label': 'Scatter', 'value': 'scatter'},
                                    {'label': 'Bar',     'value': 'bar'},
                                    {'label': 'Boxplot', 'value': 'box'}
                                ],
                                placeholder='Select visualization(s)',
                                multi=True
                            ),
                        ]
                    ),
                    # Replace the "plot here" placeholders with two Graphs:
                    html.Div(
                        className='content',
                        children=[
                            dcc.Graph(id='plot-left',  style={'height': '300px'}),
                            dcc.Graph(id='plot-right', style={'height': '300px'})
                        ]
                    )
                ]
            ),

            # The existing hidden Stores remain exactly as before
            dcc.Store(id='hovered-state', storage_type='memory'),
            dcc.Store(id='selected-state', storage_type='memory'),
            dcc.Store(
                id='manual-zoom',
                storage_type='memory',
                data={'zoom': 3, 'center': {'lat': 40.003, 'lon': -102.0517}}
            ),
        ]
    )
