import pandas as pd
import numpy as np

def get_data(filename):
    # Read data
    df = pd.read_csv(filename,
                     delimiter=',',
                     low_memory=False
                     )

    # Clean data
    df = df.dropna(subset=['Latitude', 'Longitud']).drop_duplicates(subset=['Latitude', 'Longitud'])

    # Correct the years
    df['corrected_year'] = np.where(df['YEAR'] > 24.0, 1900 + df['YEAR'], 2000 + df['YEAR'])

    return df