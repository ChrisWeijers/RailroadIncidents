from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from main import fig


app = Dash(__name__, assets_folder='assets')

app.layout = html.Div(
    children=[
        dcc.Graph(
            id='crash-map',
            figure=fig,
            className='graph-container'
        )
    ],
    style={
        "width": "100%",
        "margin": "0",
        "padding": "0",
    }
)

if __name__ == '__main__':
    app.run_server(debug=True)

