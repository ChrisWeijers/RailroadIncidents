from dash import html, dcc


def create_layout(config: list, date_min, date_max) -> html.Div:
    """
    Generates the main layout for the Dash application.

    Args:
        config (list): List of states for the states-select dropdown.
        date_min (int): Minimum year for the range slider.
        date_max (int): Maximum year for the range slider.

    Returns:
        html.Div: The Dash application layout.
    """
    # 18 items corresponding to each domain question
    viz_options = [
        # ----- (1) Analyzing Temporal Trends -----
        {
            "label": "Time Trend - Total incidents timeline (Line Chart)",
            "value": "plot_1_1",
        },
        {
            "label": "Time Trend - Incident types trends (Stream Graph)",
            "value": "plot_1_2",
        },
        {
            "label": "Time Trend - Seasonal analysis (Heat Map)",
            "value": "plot_1_3",
        },
        # ----- (2) Geographic Detail -----
        {
            "label": "Geographic Detail - Type Of Incident Per State (Sunburst Chart)",
            "value": "plot_2_1",
        },
        # ----- (3) Contributing Factors -----
        {
            "label": "Contributing Factor - Damage Distribution With Multiple Factors (Parallel Coordinate Plot)",
            "value": "plot_2_3",
        },
        {
            "label": "Contributing Factor - Severity Impact (Heat Map)",
            "value": "plot_3_2",
        },
        {
            "label": "Contributing Factor - Common Combinations (Stacked Bar Chart)",
            "value": "plot_3_3",
        },
        # ----- (4) Operator Performance -----
        {
            "label": "Operator Performance - Incident Rate Comparison (Bar Chart)",
            "value": "plot_4_1",
        },
        {
            "label": "Operator Performance - Type Distribution (Grouped Bar Chart)",
            "value": "plot_4_2",
        },
        {
            "label": "Operator Performance - Incident Type Rankings (Violin Plot)",
            "value": "plot_4_3",
        },
        # ----- (5) High-Impact Incidents -----
        {
            "label": "High Impact - Incident Codes (Sunburst Chart)",
            "value": "plot_5_2",
        },
        # ----- (6) Summarizing Incident Characteristics -----
        {
            "label": "Incident Characteristics - Most Common Types (Stacked Bar Chart)",
            "value": "plot_6_1",
        },
        {
            "label": "Incident Characteristics - Damage Cost Analysis (Violin Plot)",
            "value": "plot_6_3",
        },
    ]

    return html.Div(
        className="container",
        children=[
            html.Div(
                className="top",
                children=[
                    dcc.Graph(
                        id="barchart",
                        className="left",
                        config={"displayModeBar": False, "scrollZoom": False},
                        style={"display": "block"},
                    ),
                    dcc.Graph(
                        id="crash-map",
                        className="right",
                        config={
                            "scrollZoom": True,
                            "doubleClick": "reset",
                            "displayModeBar": False,
                        },
                    ),
                ],
            ),
            html.Div(
                className="bottom",
                children=[
                    html.Div(
                        className="dropdown-container",
                        children=[
                            dcc.RangeSlider(
                                id="range-slider",
                                className="datepicker",
                                min=int(date_min),
                                max=int(date_max),
                                step=1,
                                marks=None,
                                value=[int(date_min), int(date_max)],
                                tooltip={"placement": "bottom", "always_visible": True},
                                allowCross=False,
                            ),
                            dcc.Dropdown(
                                id="states-select",
                                className="dropdown",
                                options=[{"label": s, "value": s} for s in config],
                                multi=True,
                                placeholder="Select state(s)",
                                value=[],
                            ),
                            dcc.Dropdown(
                                id="viz-dropdown",
                                className="dropdown",
                                options=viz_options,
                                placeholder="Select a question/visualization",
                                value=None,
                                clearable=True,
                                optionHeight=80,
                            ),
                            dcc.Checklist(
                                id="show-cities",
                                className='dropdown',
                                options=[{"label": "Cities", "value": "show"}],
                                value=[],
                                style={"color": "white", "marginTop": "10px"},
                            ),
                            dcc.Checklist(
                                id="show-crossings",
                                className='dropdown',
                                options=[{"label": "Crossings", "value": "show"}],
                                value=[],
                                style={"color": "white", "marginTop": "10px"},
                            ),
                            html.Div(
                                id="zoom-level-container",
                                children=[
                                    dcc.Store(
                                        id="zoom-level", storage_type="memory", data=3  # Default zoom level
                                    ),
                                    html.Div("Adjust zoom dynamically!", className="zoom-helper"),
                                ],
                                style={"display": "none"},  # Hide or make visible as necessary
                            ),
                        ],
                    ),
                    dcc.Loading(
                        id="loading-plot",
                        type="circle",
                        overlay_style={"visibility": "visible", "filter": "blur(5px)"},
                        color='white',
                        children=[
                            html.Div(
                                className="content",
                                id="visualization-container",
                                children=[
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
            dcc.Store(id="hovered-state", storage_type="memory"),
            dcc.Store(id="selected-state", storage_type="memory"),
            dcc.Store(
                id="manual-zoom",
                storage_type="memory",
                data={"zoom": 3, "center": {"lat": 40.003, "lon": -102.0517}},
            ),
        ],
    )
