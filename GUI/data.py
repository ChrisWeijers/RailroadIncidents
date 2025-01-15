import pandas as pd
import numpy as np
import json
from typing import Tuple, Dict, Any, List


def get_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any], List, pd.DataFrame]:
    """
    Loads, cleans, and prepares the data for the Dash application.

    This function reads data from CSV files, performs data cleaning operations,
    and aggregates crash counts by state. It also loads the GeoJSON for US states.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        A tuple containing:
            - df (pd.DataFrame): The main DataFrame with accident data, cleaned and preprocessed.
            - states_center (pd.DataFrame): DataFrame containing the latitude and longitude of the center of each state.
            - state_count (pd.DataFrame): DataFrame with crash counts per state.
            - us_states (Dict[str, Any]): A dictionary containing the US states GeoJSON data.
    """
    # Read data
    df = pd.read_csv('data/railroad_incidents_fixed.csv',
                     delimiter=',',
                     low_memory=False
                     )

    fips_codes = pd.read_csv(
        'data/state_fips_master.csv',
        delimiter=',',
    )

    states_center = pd.read_csv(
        'data/states_center.csv',
        delimiter=',',
    )

    fips_codes = fips_codes[['fips', 'state_name']].copy()

    # Correct the years
    df['corrected_year'] = np.where(df['YEAR'] > 24.0, 1900 + df['YEAR'], 2000 + df['YEAR'])
    pd.to_numeric(df['corrected_year'])


    df['DATE'] = pd.to_datetime(df['corrected_year'].astype(str) + '-'
                                + df['MONTH'].astype(str) + '-'
                                + df['DAY'].astype(str),
                                errors='coerce')

    df = pd.merge(df, fips_codes, left_on='STATE', right_on='fips').drop('fips', axis=1)

    # Ensure consistent state names by stripping whitespace and standardizing case
    df['state_name'] = df['state_name'].str.strip().str.title()
    states_center['Name'] = states_center['Name'].str.strip().str.title()

    df_map = df.dropna(subset=['Latitude', 'Longitud'])

    # Load GeoJSON for US states
    with open('data/us-states.geojson', 'r') as geojson_file:
        us_states = json.load(geojson_file)

    # Aggregate crash counts by state
    state_count = df.groupby('state_name').size().reset_index(name='crash_count').sort_values(by='crash_count',
                                                                                              ascending=False)
    diff = pd.concat([states_center['Name'], state_count['state_name']]).drop_duplicates(keep=False).to_frame()
    diff.columns = ['state_name']
    diff.insert(1, 'crash_count', [0 for i in diff['state_name']])
    state_count = state_count._append(diff)

    # Create alphabetically sorted state list for dropdown
    states_alphabetical = sorted(state_count['state_name'].unique())

    return df, states_center, state_count, us_states, states_alphabetical, df_map
