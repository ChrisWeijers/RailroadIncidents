from dash import html, dcc

def create_layout(config: list, date_min, date_max, attributes, aliases) -> html.Div:
    """
    Generates the main layout for the Dash application.

    Args:
        config (list): List of states for the states-select dropdown.
        date_min (int): Minimum year for the range slider.
        date_max (int): Maximum year for the range slider.

    Returns:
        html.Div: The Dash application layout.
    """
    # Single dropdown with your 11 new visualization options:
    viz_options = [
        {
            "label": "1. Compare total accidents & hazmat cars involved (Scatter)",
            "value": "scatter_accidents_hazmat",
        },
        {
            "label": "2. Compare hazmat cars damaged/derailed & released (Scatter w/size)",
            "value": "scatter_hazmat_damaged_vs_released",
        },
        {
            "label": "3. Compare total accidents by state (Bar or Choropleth)",
            "value": "compare_accidents_by_state",
        },
        {
            "label": "4. Compare people injured/killed & hazmat cars (Scatter)",
            "value": "scatter_injured_killed_hazmat",
        },
        {
            "label": "5. Compare total damage, equipment damage, track damage (Stacked/TreeMap)",
            "value": "stacked_damage_components",
        },
        {
            "label": "6. Compare total damage & derailed loaded freight cars (Scatter)",
            "value": "scatter_damage_freight",
        },
        {
            "label": "7. Compare accidents & positive/negative drug tests (Stacked Bar)",
            "value": "stacked_drug_tests",
        },
        {
            "label": "8. Compare total accidents & train speed (Scatter)",
            "value": "scatter_accidents_speed",
        },
        {
            "label": "9. Compare people injured/killed & derailed loaded passenger cars (Scatter)",
            "value": "scatter_injured_passenger",
        },
        {
            "label": "10. Compare brakemen on duty vs. freight derailments (Clustered Bar)",
            "value": "clustered_brakemen_freight",
        },
        {
            "label": "11. Compare total damage & loaded passenger cars (Scatter)",
            "value": "scatter_damage_passenger",
        },
    ]

    return html.Div(
        className="container",
        children=[
            # -------------- Top Section (Unchanged) --------------
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
            # -------------- Bottom Section (Refactored) --------------
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
                                options=[
                                    {"label": state, "value": state} for state in config
                                ],
                                multi=True,
                                placeholder="Select state(s)",
                                value=[],
                            ),
                            dcc.Dropdown(
                                id="viz-dropdown",
                                className="dropdown",
                                options=viz_options,
                                placeholder="Select a visualization",
                                value=None,
                                clearable=True,
                            ),
                        ],
                    ),
                    html.Div(
                        className="content",
                        children=[
                            # We’ll only use plot-left here; you can use plot-right if needed
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
            # Hidden dcc.Store components remain the same if you use them
            dcc.Store(id="hovered-state", storage_type="memory"),
            dcc.Store(id="selected-state", storage_type="memory"),
            dcc.Store(
                id="manual-zoom",
                storage_type="memory",
                data={"zoom": 3, "center": {"lat": 40.003, "lon": -102.0517}},
            ),
        ],
    )
