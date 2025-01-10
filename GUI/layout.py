from dash import html, dcc
from typing import List, Dict

def create_layout(config: list, date_min, date_max, attributes, aliases) -> html.Div:
    """
    Generates the main layout for the Dash application.

    Filters attributes dynamically to ensure compatibility with aliases.
    """
    filtered_attributes = [col for col in attributes if col in aliases]

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
                            'scrollZoom': False
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
                                id='range-slider',
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
                            dcc.Dropdown(
                                id='attributes-dropdown',
                                className='dropdown',
                                options=[{'label': aliases[col], 'value': col} for col in filtered_attributes],
                                placeholder="Select an attribute",
                                value=None
                            ),
                            dcc.Dropdown(
                                id='compare-attributes-dropdown',
                                className='dropdown',
                                options=[],  # Dynamically populated
                                placeholder="Select an attribute to compare",
                                value=None
                            ),
                            dcc.Dropdown(
                                id='viz-dropdown',
                                className='dropdown',
                                options=[
                                    {'label': 'Grouped Bar Chart', 'value': 'grouped_bar'},
                                    {'label': 'Choropleth Map', 'value': 'choropleth'},
                                    {'label': 'Scatterplot', 'value': 'scatter'},
                                    {'label': 'Scatterplot with Size Encoding', 'value': 'scatter_size'},
                                    {'label': 'Scatterplot with Trendline', 'value': 'scatter_trendline'},
                                    {'label': 'Stacked Bar Chart', 'value': 'stacked_bar'},
                                    {'label': 'Side-by-Side Bar Chart', 'value': 'side_by_side_bar'},
                                    {'label': 'Clustered Bar Chart', 'value': 'clustered_bar'},
                                    {'label': 'Treemap', 'value': 'treemap'},
                                    {'label': 'Boxplot', 'value': 'boxplot'}
                                ],
                                placeholder="Select a visualization",
                                value=None
                            ),
                        ]
                    ),
                    html.Div(
                        className='content',
                        children=[
                            dcc.Graph(id='plot-left', className='content', style={'display': 'none'}),
                            dcc.Graph(id='plot-right', className='content', style={'display': 'none'})
                        ]
                    )
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
