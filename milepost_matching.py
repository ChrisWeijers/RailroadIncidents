import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
import math
import re
from typing import Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def load_milepost_data(filepath: str) -> pd.DataFrame:
    """Load and process the milepost data from CSV."""
    # Read the CSV file
    df = pd.read_csv(filepath)

    # Extract coordinates from POINT format if needed
    if 'the_geom' in df.columns:
        # Function to extract coordinates from POINT format
        def extract_coords(point_str):
            try:
                coords = point_str.replace('POINT (', '').replace(')', '').split()
                return pd.Series({'LONG': float(coords[0]), 'LAT': float(coords[1])})
            except (ValueError, IndexError):
                return pd.Series({'LONG': np.nan, 'LAT': np.nan})

        # Extract coordinates and add as new columns if they don't exist
        if 'LAT' not in df.columns or 'LONG' not in df.columns:
            coords_df = df['the_geom'].apply(extract_coords)
            df = pd.concat([df, coords_df], axis=1)

    # Ensure numeric types for coordinates
    for col in ['LAT', 'LONG']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Clean 'MILEPOST' field
    df['MILEPOST_CLEAN'] = df['MILEPOST'].apply(extract_numeric_milepost)

    return df

def load_crash_data(filepath: str) -> pd.DataFrame:
    """Load and clean the crash data from CSV."""
    # Read the CSV file
    df = pd.read_csv(filepath, low_memory=False)

    # Convert date columns
    date_columns = ['YEAR', 'MONTH', 'DAY']
    if all(col in df.columns for col in date_columns):
        # Handle potential missing or invalid values
        for col in date_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Create DATE column where all components are valid
        valid_dates = df[date_columns].notna().all(axis=1)
        df['DATE'] = pd.NaT  # Initialize with NaT (Not a Time)
        df.loc[valid_dates, 'DATE'] = pd.to_datetime(
            df.loc[valid_dates, date_columns],
            errors='coerce'
        )

    # Clean coordinates
    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitud'] = pd.to_numeric(df['Longitud'], errors='coerce')

    # Clean 'MILEPOST' field
    df['MILEPOST_CLEAN'] = df['MILEPOST'].apply(extract_numeric_milepost)

    return df

def extract_numeric_milepost(milepost_str):
    """Extract numeric value from a milepost string."""
    if pd.isna(milepost_str):
        return np.nan
    # Use regular expression to extract numbers and decimal points
    match = re.findall(r"[-+]?\d*\.\d+|\d+", str(milepost_str))
    if match:
        try:
            return float(match[0])
        except ValueError:
            return np.nan
    return np.nan

def find_nearest_mileposts(crash_df: pd.DataFrame, milepost_df: pd.DataFrame) -> pd.DataFrame:
    """Find the nearest milepost for crashes with coordinates using BallTree."""
    # Crashes with coordinates
    crashes_with_coords = crash_df.dropna(subset=['Latitude', 'Longitud']).copy()
    # Mileposts with coordinates
    mileposts_with_coords = milepost_df.dropna(subset=['LAT', 'LONG']).copy()

    # Convert degrees to radians
    crashes_with_coords['Latitude_rad'] = np.deg2rad(crashes_with_coords['Latitude'])
    crashes_with_coords['Longitud_rad'] = np.deg2rad(crashes_with_coords['Longitud'])
    mileposts_with_coords['LAT_rad'] = np.deg2rad(mileposts_with_coords['LAT'])
    mileposts_with_coords['LONG_rad'] = np.deg2rad(mileposts_with_coords['LONG'])

    # Build BallTree
    milepost_tree = BallTree(
        mileposts_with_coords[['LAT_rad', 'LONG_rad']].values,
        metric='haversine'
    )

    # Query BallTree for nearest mileposts
    distances, indices = milepost_tree.query(
        crashes_with_coords[['Latitude_rad', 'Longitud_rad']].values,
        k=1
    )

    # Convert distances from radians to meters
    earth_radius = 6371000  # meters
    distances_meters = distances.flatten() * earth_radius

    # Get nearest milepost info
    nearest_mileposts = mileposts_with_coords.iloc[indices.flatten()].reset_index(drop=True)
    crashes_with_coords = crashes_with_coords.reset_index(drop=True)
    crashes_with_coords['Nearest_LAT'] = nearest_mileposts['LAT']
    crashes_with_coords['Nearest_LONG'] = nearest_mileposts['LONG']
    crashes_with_coords['Distance_meters'] = distances_meters

    return crashes_with_coords

def find_nearest_milepost_by_number(crash_df: pd.DataFrame, milepost_df: pd.DataFrame) -> pd.DataFrame:
    """Find nearest mileposts for crashes without coordinates but with milepost numbers."""
    # Filter crashes without coordinates but with 'MILEPOST_CLEAN' and 'RAILROAD'
    crashes_no_coords = crash_df[
        crash_df['Latitude'].isna() &
        crash_df['Longitud'].isna() &
        crash_df['MILEPOST_CLEAN'].notna() &
        crash_df['RAILROAD'].notna()
        ].copy()

    # Clean 'RAILROAD' entries
    crashes_no_coords['RAILROAD'] = crashes_no_coords['RAILROAD'].str.strip().str.upper()
    milepost_df['RAILROAD'] = milepost_df['RAILROAD'].str.strip().str.upper()

    # Prepare milepost data for matching
    milepost_df_filtered = milepost_df[
        milepost_df['MILEPOST_CLEAN'].notna() &
        milepost_df['RAILROAD'].notna()
        ].copy()

    # Ensure 'MILEPOST_CLEAN' is float
    crashes_no_coords['MILEPOST_CLEAN'] = pd.to_numeric(crashes_no_coords['MILEPOST_CLEAN'], errors='coerce')
    milepost_df_filtered['MILEPOST_CLEAN'] = pd.to_numeric(milepost_df_filtered['MILEPOST_CLEAN'], errors='coerce')

    # Drop rows where conversion to float failed
    crashes_no_coords = crashes_no_coords.dropna(subset=['MILEPOST_CLEAN'])
    milepost_df_filtered = milepost_df_filtered.dropna(subset=['MILEPOST_CLEAN'])

    # Select and rename columns for milepost data to avoid conflicts
    milepost_df_filtered = milepost_df_filtered[['RAILROAD', 'MILEPOST_CLEAN', 'LAT', 'LONG']].copy()
    milepost_df_filtered = milepost_df_filtered.rename(columns={
        'MILEPOST_CLEAN': 'MILEPOST_REF',
        'LAT': 'Nearest_LAT',
        'LONG': 'Nearest_LONG'
    })

    # Process each railroad separately
    results = []
    for railroad in crashes_no_coords['RAILROAD'].unique():
        # Get data for this railroad
        railroad_crashes = crashes_no_coords[crashes_no_coords['RAILROAD'] == railroad].copy()
        railroad_mileposts = milepost_df_filtered[milepost_df_filtered['RAILROAD'] == railroad].copy()

        # Sort by milepost number
        railroad_crashes = railroad_crashes.sort_values('MILEPOST_CLEAN')
        railroad_mileposts = railroad_mileposts.sort_values('MILEPOST_REF')

        # Perform merge_asof for this railroad
        if not railroad_crashes.empty and not railroad_mileposts.empty:
            merged = pd.merge_asof(
                railroad_crashes,
                railroad_mileposts,
                left_on='MILEPOST_CLEAN',
                right_on='MILEPOST_REF',
                direction='nearest'
            )

            # Calculate distance between mileposts
            merged['Distance_milepost'] = abs(merged['MILEPOST_CLEAN'] - merged['MILEPOST_REF'])
            results.append(merged)

    # Combine results from all railroads
    if results:
        merged = pd.concat(results, ignore_index=True)
    else:
        # Return empty DataFrame with correct columns if no matches found
        merged = pd.DataFrame(
            columns=list(crashes_no_coords.columns) + ['Nearest_LAT', 'Nearest_LONG', 'Distance_milepost'])

    return merged

def create_dashboard(crash_df: pd.DataFrame, milepost_df: pd.DataFrame) -> go.Figure:
    """Create an enhanced dashboard with multiple visualizations."""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Railroad Crashes and Mileposts in the United States',
            'Crashes by Year',
            'Top 10 Railroads by Crash Count',
            'Top 10 States by Crash Count'
        ),
        specs=[
            [{"type": "mapbox", "colspan": 2}, None],
            [{"type": "bar"}, {"type": "bar"}]
        ],
        column_widths=[0.5, 0.5],
        row_heights=[0.6, 0.4],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )

    # Enhanced map of crashes and mileposts
    fig.add_trace(
        go.Scattermapbox(
            lat=milepost_df['LAT'].dropna(),
            lon=milepost_df['LONG'].dropna(),
            mode='markers',
            marker=dict(
                size=4,
                color='blue',
                opacity=0.6
            ),
            name='Mileposts',
            hovertext=milepost_df.apply(
                lambda x: f"Railroad: {x['RAILROAD']}<br>Milepost: {x['MILEPOST']}<br>Coordinates: ({x['LAT']:.4f}, {x['LONG']:.4f})",
                axis=1
            ),
            hoverinfo='text'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scattermapbox(
            lat=crash_df['Latitude'].dropna(),
            lon=crash_df['Longitud'].dropna(),
            mode='markers',
            marker=dict(
                size=6,
                color='red',
                opacity=0.7
            ),
            name='Crashes',
            hovertext=crash_df.apply(
                lambda x: f"Date: {x['DATE']}<br>Railroad: {x['RAILROAD']}<br>State: {x['STATE']}<br>Coordinates: ({x['Latitude']:.4f}, {x['Longitud']:.4f})",
                axis=1
            ),
            hoverinfo='text'
        ),
        row=1, col=1
    )

    # Crashes by year with enhanced styling
    yearly_crashes = crash_df['YEAR'].value_counts().sort_index()
    fig.add_trace(
        go.Bar(
            x=yearly_crashes.index,
            y=yearly_crashes.values,
            name='Crashes by Year',
            marker_color='rgb(158,202,225)',
            hovertemplate='Year: %{x}<br>Crashes: %{y:,}<extra></extra>'
        ),
        row=2, col=1
    )

    # Top 10 railroads by crash count
    railroad_crashes = crash_df['RAILROAD'].value_counts().head(10)
    fig.add_trace(
        go.Bar(
            x=railroad_crashes.index,
            y=railroad_crashes.values,
            name='Crashes by Railroad',
            marker_color='rgb(94,158,217)',
            hovertemplate='Railroad: %{x}<br>Crashes: %{y:,}<extra></extra>'
        ),
        row=2, col=2
    )

    # Update layout with enhanced styling
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",  # Clean, modern map style
            center=dict(lat=39.8283, lon=-98.5795),
            zoom=3,
            bearing=0,
            pitch=0
        ),
        height=900,  # Increased height for better visibility
        showlegend=True,
        title=dict(
            text="Railroad Crash Analysis Dashboard",
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=24)
        ),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255,255,255,0.8)'
        ),
        margin=dict(l=60, r=60, t=80, b=30)
    )

    # Update axes labels and styling
    fig.update_xaxes(title_text="Year", row=2, col=1)
    fig.update_xaxes(title_text="Railroad", row=2, col=2)
    fig.update_yaxes(title_text="Number of Crashes", row=2, col=1)
    fig.update_yaxes(title_text="Number of Crashes", row=2, col=2)

    return fig

def get_plotting_statistics(crash_df: pd.DataFrame, milepost_df: pd.DataFrame) -> dict:
    """Calculate statistics about the plotted data."""
    stats = {
        'total_crashes': len(crash_df),
        'crashes_with_coords': len(crash_df.dropna(subset=['Latitude', 'Longitud'])),
        'crashes_with_milepost_only': len(crash_df[
            (crash_df['Latitude'].isna() | crash_df['Longitud'].isna()) &
            crash_df['MILEPOST_CLEAN'].notna()
        ]),
        'total_mileposts': len(milepost_df),
        'mileposts_with_coords': len(milepost_df.dropna(subset=['LAT', 'LONG'])),
        'crashes_matched_to_mileposts': len(crash_df.dropna(subset=['Nearest_LAT', 'Nearest_LONG'])),
        'unique_railroads': len(pd.concat([
            crash_df['RAILROAD'].dropna(),
            milepost_df['RAILROAD'].dropna()
        ]).unique()),
        'date_range': f"{int(crash_df['YEAR'].min())} to {int(crash_df['YEAR'].max())}"
    }

    # Calculate percentage of crashes successfully mapped
    stats['mapping_success_rate'] = round(
        stats['crashes_matched_to_mileposts'] /
        stats['total_crashes'] * 100, 2
    )

    return stats

def main(milepost_filepath: str, crash_filepath: str) -> Tuple[pd.DataFrame, go.Figure, dict]:
    """Main function to process data and create visualization."""
    # Load and clean data
    print("Loading milepost data...")
    milepost_df = load_milepost_data(milepost_filepath)
    print(f"Loaded {len(milepost_df)} milepost records")

    print("\nLoading crash data...")
    crash_df = load_crash_data(crash_filepath)
    print(f"Loaded {len(crash_df)} crash records")

    print("\nMatching crashes to mileposts using coordinates...")
    # Find nearest mileposts for crashes with coordinates
    crashes_with_coords = find_nearest_mileposts(crash_df, milepost_df)

    print("\nMatching crashes to mileposts using milepost numbers...")
    # Find nearest mileposts for crashes without coordinates but with 'MILEPOST_CLEAN' and 'RAILROAD'
    crashes_no_coords = find_nearest_milepost_by_number(crash_df, milepost_df)

    # Combine the results
    crash_df_matched = pd.concat([crashes_with_coords, crashes_no_coords], ignore_index=True)

    print("\nCreating dashboard...")
    # Create dashboard
    dashboard = create_dashboard(crash_df_matched, milepost_df)

    # Get statistics
    stats = get_plotting_statistics(crash_df_matched, milepost_df)

    return crash_df_matched, dashboard, stats


# Example usage
if __name__ == "__main__":
    milepost_filepath = 'data/Rail_Mileposts_20241126.csv'
    crash_filepath = 'data/Railroad_Equipment_Accident_Incident.csv'

    crash_df_matched, dashboard, stats = main(milepost_filepath, crash_filepath)

    # Display the dashboard
    dashboard.show()

    # Print statistics
    print("\nData Plotting Statistics:")
    print("-----------------------")
    print(f"Total crashes in dataset: {stats['total_crashes']:,}")
    print(f"Crashes with direct coordinates: {stats['crashes_with_coords']:,}")
    print(f"Crashes with milepost only: {stats['crashes_with_milepost_only']:,}")
    print(f"Crashes successfully matched to mileposts: {stats['crashes_matched_to_mileposts']:,}")
    print(f"Overall mapping success rate: {stats['mapping_success_rate']}%")
    print("\nMilepost Information:")
    print(f"Total mileposts: {stats['total_mileposts']:,}")
    print(f"Mileposts with valid coordinates: {stats['mileposts_with_coords']:,}")
    print("\nDataset Coverage:")
    print(f"Unique railroads: {stats['unique_railroads']:,}")
    print(f"Date range: {stats['date_range']}")

