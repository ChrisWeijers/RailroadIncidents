from dash import Dash
from GUI.layout import create_layout
from GUI.callbacks import setup_callbacks
from GUI.config import aliases, config, viz_options
from GUI.data import get_data

# Load in the data
df, states_center, state_count, us_states, states_alphabetical, city_data, crossing_data = get_data()

# Set up the dashboard
app = Dash(__name__)
app.title = 'US Railroad Incidents'

# App Layout
app.layout = create_layout(config, df['corrected_year'].min(), df['corrected_year'].max(), viz_options)

# Set up callbacks with all required arguments
setup_callbacks(app, df, state_count, us_states, states_center, aliases, city_data, crossing_data)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_ui=False)
