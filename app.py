from dash import Dash
from GUI.layout import create_layout
from GUI.callbacks import setup_callbacks
from GUI.config import config, date_min, date_max, attributes
from GUI.alias import aliases  # Import aliases
from GUI.data import get_data

df, states_center, state_count, us_states, states_alphabetical, df_map, city_data, crossing_data = get_data()

app = Dash(__name__)
app.title = 'US Railroad Incidents'

# App Layout
app.layout = create_layout(config, date_min, date_max, attributes, aliases, city_data)

# Set up callbacks with all required arguments
setup_callbacks(app, df, state_count, us_states, df_map, states_center, aliases, city_data, crossing_data)


if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_ui=False)
