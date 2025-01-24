from dash import html, dcc


def create_layout(config: list, date_min, date_max, viz_options) -> html.Div:
    """
    Generates the main layout for the Dash application.

    Args:
        config (list): List of states for the states-select dropdown.
        date_min (int): Minimum year for the range slider.
        date_max (int): Maximum year for the range slider.
        viz_options (list(dict)): list of all visualization options for the dropdown.

    Returns:
        html.Div: The Dash application layout.
    """

    return html.Div(
        className="container",
        children=[
            # The top section of the dashboard
            html.Div(
                className="top",
                children=[
                    # The barchart and map
                    dcc.Graph(
                        id="barchart",
                        className="left",  # Get the barchart in the left part
                        config={"displayModeBar": False, "scrollZoom": False},
                    ),
                    dcc.Graph(
                        id="crash-map",
                        className="right",  # Get the map in the right part
                        config={
                            "scrollZoom": True,
                            "doubleClick": "reset",
                            "displayModeBar": False,
                        },
                    ),
                ],
            ),
            # The bottom section of the dashboard
            html.Div(
                className="bottom",
                children=[
                    html.Div(
                        # All the different selection items
                        className="dropdown-container",
                        children=[
                            dcc.RangeSlider(
                                # Slider for changing the year
                                id="range-slider",
                                className="datepicker",
                                min=int(date_min),  # Start with year of first crash
                                max=int(date_max),  # End with year of last crash
                                step=1,
                                marks=None,
                                value=[int(date_min), int(date_max)],  # Set the value as full range to begin with
                                tooltip={"placement": "bottom", "always_visible": True},  # Show what range is selected
                                allowCross=False,
                            ),
                            dcc.Dropdown(
                                # Dropdown for selecting the state(s)
                                id="states-select",
                                className="dropdown",
                                options=[{"label": s, "value": s} for s in config],  # Get all states in the dropdown in alphabetical order
                                multi=True,  # Make sure multiple states can be selected
                                placeholder="Select state(s)",
                                value=[],
                            ),
                            dcc.Dropdown(
                                # Dropdown for selecting the visualization for the bottom section
                                id="viz-dropdown",
                                className="dropdown",
                                options=viz_options,  # Initialize all the visualization options
                                placeholder="Select a visualization",
                                value=None,
                                clearable=True,
                                optionHeight=80,  # Make sure the options do not overlap
                            ),
                            dcc.Checklist(
                                # Toggle cities
                                id="show-cities",
                                className='dropdown',
                                options=[{"label": "Cities", "value": "show"}],
                                value=[],
                                style={"color": "white", "marginTop": "10px"},
                            ),
                            dcc.Checklist(
                                # Toggle crossings
                                id="show-crossings",
                                className='dropdown',
                                options=[{"label": "Crossings", "value": "show"}],
                                value=[],
                                style={"color": "white", "marginTop": "10px"},
                            ),
                            html.Div(
                                # Store the zoom level
                                id="zoom-level-container",
                                children=[
                                    dcc.Store(
                                        id="zoom-level", storage_type="memory", data=3  # Default zoom level
                                    ),
                                    html.Div("Adjust zoom dynamically!", className="zoom-helper"),
                                ],
                                style={"display": "none"},  # Hide
                            ),
                        ],
                    ),
                    dcc.Loading(
                        # Get loading spinner for the bottom section
                        id="loading-plot",
                        type="circle",  # Set it as circle spinner
                        overlay_style={"visibility": "visible", "filter": "blur(5px)"},  # Blur background when loading
                        color='white',  # Set color
                        children=[
                            # Bottom section for the visualization
                            html.Div(
                                className="content",
                                id="visualization-container",
                                children=[
                                    # Start with text
                                    html.Div(
                                        'Oops! It seems like you haven’t selected a visualization. Pick one from the '
                                        'to see the magic!',
                                        id='no-viz-text',
                                        className='content',
                                        style={"textAlign": "center", "color": "gray", "fontSize": "16px"},
                                    )
                                ],
                            ),
                        ]
                    )
                ],
            ),
            # Store objects needed for callbacks
            dcc.Store(id="hovered-state", storage_type="memory"),
            dcc.Store(id="selected-state", storage_type="memory"),
            dcc.Store(
                id="manual-zoom",
                storage_type="memory",
                data={"zoom": 3, "center": {"lat": 40.003, "lon": -102.0517}},  # Center of US with accompanying zoom level
            ),
        ],
    )
