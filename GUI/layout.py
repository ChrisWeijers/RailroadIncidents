from dash import html, dcc

def create_layout(config: list, date_min, date_max, attributes, aliases, city_data) -> html.Div:
    """
    Generates the main layout for the Dash application.

    Args:
        config (list): List of states for the states-select dropdown.
        date_min (int): Minimum year for the range slider.
        date_max (int): Maximum year for the range slider.
        attributes (list): Additional attributes if needed (placeholder).
        aliases (dict): Aliases for advanced labeling (placeholder).

    Returns:
        html.Div: The Dash application layout.
    """
    # 18 items corresponding to each domain question
    viz_options = [
        # ----- (1) Analyzing Temporal Trends -----
        {
            "label": "Are total incidents increasing/decreasing over time?",
            "value": "plot_1_1",
        },
        {
            "label": "Which incident types show biggest changes over time?",
            "value": "plot_1_2",
        },
        {
            "label": "Any noticeable seasonal patterns?",
            "value": "plot_1_3",
        },
        # ----- (2) Spatial Patterns -----
        {
            "label": "Highest geographic concentration of incidents?",
            "value": "plot_2_1",
        },
        {
            "label": "Distribution differences for various incident types?",
            "value": "plot_2_3",
        },

        {
            "label": "How do these factors affect severity (damage, injuries)?",
            "value": "plot_3_2",
        },
        {
            "label": "Specific factor combos that often precede incidents?",
            "value": "plot_3_3",
        },
        # ----- (4) Operator Performance -----
        {
            "label": "Compare overall incident rates across operators",
            "value": "plot_4_1",
        },
        {
            "label": "Differences in incident types by operator",
            "value": "plot_4_2",
        },
        {
            "label": "Which operator is higher/lower for specific incidents?",
            "value": "plot_4_3",
        },
        # ----- (5) High-Impact Incidents -----
        {
            "label": "Primary & secondary causes of high-impact incidents?",
            "value": "plot_5_1",
        },
        {
            "label": "Common circumstances in these severe incidents?",
            "value": "plot_5_2",
        },
        {
            "label": "Preventable factors in high-impact incidents?",
            "value": "plot_5_3",
        },
        # ----- (6) Summarizing Incident Characteristics -----
        {
            "label": "Most common types of railroad incidents?",
            "value": "plot_6_1",
        },
        {
            "label": "Most frequently cited primary causes?",
            "value": "plot_6_2",
        },
        {
            "label": "Avg damage cost among different incident types?",
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
                    html.Div(
                        className="content",
                        children=[
                            dcc.Graph(
                                id="plot-left",
                                className="content",
                                style={"display": "none"},
                            ),
                            html.Div(
                                'No visualization selected. Choose a visualization in the dropdown...',
                                id='plot-right',
                                className='content',
                            )
                        ],
                    ),
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
