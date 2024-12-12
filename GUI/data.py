import pandas as pd
import numpy as np
import json
from typing import Tuple, Dict, Any


def get_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
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
    df = pd.read_csv('data/Railroad_Equipment_Accident_Incident.csv',
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
    # Clean data
    df = df.dropna(subset=['Latitude', 'Longitud'])

    # Correct the years
    df['corrected_year'] = np.where(df['YEAR'] > 24.0, 1900 + df['YEAR'], 2000 + df['YEAR'])

    df = pd.merge(df, fips_codes, left_on='STATE', right_on='fips').drop('fips', axis=1)

    # Ensure consistent state names by stripping whitespace and standardizing case
    df['state_name'] = df['state_name'].str.strip().str.title()
    states_center['Name'] = states_center['Name'].str.strip().str.title()

    # Load GeoJSON for US states
    with open('data/us-states.geojson', 'r') as geojson_file:
        us_states = json.load(geojson_file)

    # Aggregate crash counts by state
    state_count = df.groupby('state_name').size().reset_index(name='crash_count').sort_values(by='crash_count',
                                                                                              ascending=False)
    diff = pd.concat([states_center['Name'], state_count['state_name']]).drop_duplicates(keep=False).to_frame()
    diff.columns = ['state_name']
    diff.insert(1, 'crash_count', [0, 0, 0])
    state_count = state_count._append(diff)

    return df, states_center, state_count, us_states
