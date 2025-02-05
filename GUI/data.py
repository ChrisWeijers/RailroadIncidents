import pandas as pd
import numpy as np
import json
from typing import Tuple, Dict, Any
from pandas import DataFrame


def get_data() -> tuple[DataFrame, DataFrame, Any, Any, list[Any], Any, DataFrame]:
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
            - states_alphabetical (List[str]): A list containing the US states in alphabetical order.
            - city_data (pd.Dataframe): Dataframe containing data about cities in the US.
            - crossing_data (pd.Dataframe): Dataframe containing data about railroad crossing in the US.
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

    # Create date attribute
    df['DATE'] = pd.to_datetime(df['corrected_year'].astype(str) + '-'
                                + df['MONTH'].astype(str) + '-'
                                + df['DAY'].astype(str),
                                errors='coerce')

    # Create year+month attribute
    df['DATE_M'] = pd.to_datetime(df['corrected_year'].astype(str) + '-'
                                  + df['MONTH'].astype(str),
                                  errors='coerce')

    # Add fips code to the data matching STATE
    df = pd.merge(df, fips_codes, left_on='STATE', right_on='fips').drop('fips', axis=1)

    # Ensure consistent state names by stripping whitespace and standardizing case
    df['state_name'] = df['state_name'].str.strip().str.title()
    states_center['Name'] = states_center['Name'].str.strip().str.title()

    # Load GeoJSON for US states
    with open('data/us-states.geojson', 'r') as geojson_file:
        us_states = json.load(geojson_file)

    # Aggregate crash counts by state and make sure all states are added
    state_count = df.groupby('state_name').size().reset_index(name='crash_count').sort_values(by='crash_count',
                                                                                              ascending=False)
    diff = pd.concat([states_center['Name'], state_count['state_name']]).drop_duplicates(keep=False).to_frame()
    diff.columns = ['state_name']
    diff.insert(1, 'crash_count', [0 for i in diff['state_name']])
    state_count = state_count._append(diff)

    # Create alphabetically sorted state list for dropdown
    states_alphabetical = sorted(state_count['state_name'].unique())

    # Add city data
    city_data = pd.read_csv('data/city_data.csv', delimiter=',', low_memory=False)
    city_data = city_data[city_data['population'] > 50000]

    # Add crossing data
    crossing_data = pd.read_csv('data/crossing_data_rerevised.csv', delimiter=',', low_memory=False)

    # Ensure Latitude and Longitude are numeric
    crossing_data['Latitude'] = pd.to_numeric(crossing_data['Latitude'], errors='coerce')
    crossing_data['Longitude'] = pd.to_numeric(crossing_data['Longitude'], errors='coerce')

    # Drop rows with invalid coordinates
    crossing_data = crossing_data.dropna(subset=['Latitude', 'Longitude'])

    # Limit the number of renderings due to dash computational limitations
    if len(crossing_data) > 10000:
        crossing_data = crossing_data.sample(n=10000, random_state=42)

    return df, states_center, state_count, us_states, states_alphabetical, city_data, crossing_data
