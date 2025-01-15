from dash import html, dcc

def create_layout(config: list, date_min, date_max, attributes, aliases) -> html.Div:
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
            "label": "1.1 Are total incidents increasing/decreasing over time?",
            "value": "plot_1_1",
        },
        {
            "label": "1.2 Which incident types show biggest changes over time?",
            "value": "plot_1_2",
        },
        {
            "label": "1.3 Any noticeable seasonal patterns?",
            "value": "plot_1_3",
        },
        # ----- (2) Spatial Patterns -----
        {
            "label": "2.1 Highest geographic concentration of incidents?",
            "value": "plot_2_1",
        },
        {
            "label": "2.2 Geographic factors (urban, mountains) vs. incident rates?",
            "value": "plot_2_2",
        },
        {
            "label": "2.3 Distribution differences for various incident types?",
            "value": "plot_2_3",
        },
        # ----- (3) Contributing Factors -----
        {
            "label": "3.1 Which factors (speed, weather, track) correlate strongly?",
            "value": "plot_3_1",
        },
        {
            "label": "3.2 How do these factors affect severity (damage, injuries)?",
            "value": "plot_3_2",
        },
        {
            "label": "3.3 Specific factor combos that often precede incidents?",
            "value": "plot_3_3",
        },
        # ----- (4) Operator Performance -----
        {
            "label": "4.1 Compare overall incident rates across operators",
            "value": "plot_4_1",
        },
        {
            "label": "4.2 Differences in incident types by operator",
            "value": "plot_4_2",
        },
        {
            "label": "4.3 Which operator is higher/lower for specific incidents?",
            "value": "plot_4_3",
        },
        # ----- (5) High-Impact Incidents -----
        {
            "label": "5.1 Primary & secondary causes of high-impact incidents?",
            "value": "plot_5_1",
        },
        {
            "label": "5.2 Common circumstances in these severe incidents?",
            "value": "plot_5_2",
        },
        {
            "label": "5.3 Preventable factors in high-impact incidents?",
            "value": "plot_5_3",
        },
        # ----- (6) Summarizing Incident Characteristics -----
        {
            "label": "6.1 Most common types of railroad incidents?",
            "value": "plot_6_1",
        },
        {
            "label": "6.2 Most frequently cited primary causes?",
            "value": "plot_6_2",
        },
        {
            "label": "6.3 Avg damage cost among different incident types?",
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
                            dcc.Graph(
                                id="plot-right",
                                className="content",
                                style={"display": "none"},
                            ),
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
