from dash import Dash
from GUI.layout import create_layout
from GUI.callbacks import setup_callbacks
from GUI.config import config, date_min, date_max, attributes
from GUI.data import get_data

# Initialize data
df, states_center, state_count, us_states, states_alphabetical, df_map = get_data()

app = Dash(__name__)
app.title = 'Railroad Dashboard'

# App Layout
app.layout = create_layout(config, date_min, date_max, attributes)

# Set up callbacks
setup_callbacks(app, df, state_count, us_states, df_map)

if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_ui=True)
