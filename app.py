from dash import Dash
from GUI.layout import create_layout
from GUI.callbacks import setup_callbacks
from GUI.config import config, date_min, date_max, attributes
from GUI.alias import aliases  # Import aliases


app = Dash(__name__)
app.title = 'Railroad Dashboard'

# App Layout
app.layout = create_layout(config, date_min, date_max, attributes, aliases)

# Set up callbacks with all required arguments
setup_callbacks(app, aliases)

if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_ui=True)
