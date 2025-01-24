<div align="center">

# Data Visualization Dashboard (Railroad Incidents)

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Last Commit](https://img.shields.io/github/last-commit/ChrisWeijers/RailroadIncidents)

</div>

A Dash-based dashboard for visualizing railroad-related incidents across U.S. states. This project combines data from various CSV files, processes and cleans the information, and presents multiple interactive charts and maps. The goal is to help users quickly explore historic incident data, geographic trends, and potentially discover insights on railroad safety.

## Features

- Displays an interactive map of railroad incidents by U.S. state.  
- Offers state-level crash counts and city-level data for incidents in larger population areas.  
- Integrates crossing data to show relevant markers on the map (selectively sampled to optimize performance).  
- Allows users to filter incidents by date, select specific states, display city or crossing layers, and dynamically update charts.  
- Supports additional data exploration through bar charts or other visualizations to help identify trends.

`app.py`

Entry point for the Dash application. It creates the Dash instance, sets up the layout, and registers callbacks.

`GUI/data.py`

Loads, cleans, and prepares the data from multiple CSV files. Merges in geographic data, adjusts date fields, performs sampling on crossing data, and returns these datasets for the dashboard.

`GUI/layout.py`

Defines the application layout (the user interface) with Dash components such as dropdowns, date pickers, and placeholders for plots.

`GUI/callbacks.py`

Sets up the interactive callbacks that connect the UI elements to the data. Responds to user inputs, updates charts and maps, and manages filter logic.

`GUI/config.py`

Holds global settings, including calculated boundaries for data ranges (e.g., minimum and maximum dates, attribute value limits) and a rough geographical outline of the U.S. It also standardizes attribute naming conventions using dictionaries for aliases, groups, and type mappings, ensuring consistency across the user interface.

`assets/stylesheet.css`

Custom CSS to override default Dash and browser styling, improving the visual consistency and layout of the dashboard.

`data/`

Contains the CSV files for incident data, city data, state FIPS codes, and other information needed to build the analyses and maps.

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ChrisWeijers/RailroadIncidents.git

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt

    ```
    or
    ```bash
    pip install dash plotly pandas geopandas numpy shapely
    ```
3. **Verify Data Files:**
   Ensure that the CSV files referenced in the data folder are present and in the correct locations. These files are relatively large, so consider verifying that your system can handle them.

4. **Run the application:**
   ```bash
   python app.py
   ```
   By default, the Dash server will start listening on [http://127.0.0.1:8050](http://127.0.0.1:8050). Open your browser and visit that address to see the dashboard.
   
---

## Usage
1. **Map Component:**
   - Displays states color-coded by number of incidents.
   - Hover over states to hightlight them.
   - Zoom in/out or drag the map around.
2. **Filters:**
   - Date range filters for incident year.
   - State selection dropdown to focus on specific areas.
   - Options to toggle city data or crossing data on the map.
4. **Charts:**
   - Dynamic charts (e.g., bar charts) update based on current filter state or map selections.
   - Explore relationships between different attributes—accident damage, injuries, etc.
  
---
## Customization
- Adjust or add new visualizations in `GUI/plots.py` for more detailed analytics and different chart types.
- Switch out data sources or incorporate new CSV files by editing `GUI/data.py`.
- Modify the overall page layout in `GUI/layout.py` and `assets/stylesheet.css` to adjust the design.

## License
The Railroad Incidents visualization dashboard is open-sourced software licensed under the [MIT license](https://github.com/ChrisWeijers/RailroadIncidents/blob/main/LICENSE.md).

## Contact
- **Bjorn Albers** - [@pythoniaan](https://github.com/pythoniaan)
- **Bilgin Eren** - [@bilginn7](https://github.com/bilginn7)
- **Junior Jansen** - [@JuniorJansen](https://github.com/JuniorJansen)
- **Chris Weijers** - [@ChrisWeijers](https://github.com/ChrisWeijers)
