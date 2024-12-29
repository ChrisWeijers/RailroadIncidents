import pandas as pd
import requests
import random
import logging
from typing import Optional, Dict, List
import time
from thefuzz import fuzz
import json
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='geocoding_debug.log'
)


def geocode(query: str) -> List[Dict]:
    """
    Make a request to the Photon (Komoot) API with better error handling and logging.
    """
    logging.info(f"Attempting to geocode query: {query}")
    url = "https://photon.komoot.io/api/"
    params = {"q": query}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        results = []
        for feature in features:
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [])

            if len(coords) == 2:
                longitude, latitude = coords
                results.append({
                    "name": props.get("name", ""),
                    "type": props.get("type", ""),
                    "longitude": longitude,
                    "latitude": latitude,
                    "properties": props
                })

        logging.info(f"Found {len(results)} results for query: {query}")
        return results

    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed for query '{query}': {str(e)}")
        return []
    except ValueError as e:
        logging.error(f"JSON parsing failed for query '{query}': {str(e)}")
        return []


def find_railway_matches(results: List[Dict]) -> List[Dict]:
    """
    Filter results to only those containing 'railway' in their properties.
    """
    railway_matches = []
    for r in results:
        props = r.get("properties", {})
        property_values = [str(v).lower() for v in props.values()]
        if any('railway' in val for val in property_values):
            railway_matches.append(r)
    return railway_matches


def get_fallback_queries(station: str, trkname: str, county: str, state_str: str) -> List[str]:
    """
    Build a list of fallback queries with decreasing specificity and various rail yard alternatives.
    """
    queries = []

    # 1. Try with original details
    if all([station, trkname, county, state_str]):
        queries.append(f"{station}, {trkname}, {county}, {state_str}")

    # 2. Try with yard variations of track name
    if all([station, county, state_str]):
        queries.extend([
            f"{station}, train yard, {county}, {state_str}",
            f"{station}, railway yard, {county}, {state_str}",
            f"{station}, railroad yard, {county}, {state_str}",
            f"{station}, yard, {county}, {state_str}"
        ])

    # 3. Try without track name but with county
    if all([station, county, state_str]):
        queries.extend([
            f"{station} train yard, {county}, {state_str}",
            f"{station} railway yard, {county}, {state_str}",
            f"{station} railroad yard, {county}, {state_str}",
            f"{station} yard, {county}, {state_str}",
            f"{station}, {county}, {state_str}"
        ])

    # 4. Try with just station and state
    if station and state_str:
        queries.extend([
            f"{station} train yard, {state_str}",
            f"{station} railway yard, {state_str}",
            f"{station} railroad yard, {state_str}",
            f"{station} yard, {state_str}",
            f"{station}, {state_str}"
        ])

    # Remove any duplicates while preserving order
    seen = set()
    return [x for x in queries if not (x in seen or seen.add(x))]


class LocationCache:
    """Cache for storing known location corrections"""
    def __init__(self, cache_file: str = "location_corrections.json"):
        self.cache_file = Path(cache_file)
        self.corrections = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load existing corrections from file"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}

    def save_cache(self):
        """Save corrections to file"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.corrections, f, indent=2)

    def get_correction(self, location: str, state: str) -> Optional[str]:
        """Get corrected name for a location if it exists"""
        key = f"{location.lower()},{state.lower()}"
        return self.corrections.get(key)

    def add_correction(self, original: str, corrected: str, state: str):
        """Add a new correction to the cache"""
        key = f"{original.lower()},{state.lower()}"
        self.corrections[key] = corrected
        self.save_cache()

def get_city_suggestions(state: str) -> List[str]:
    """
    Get list of cities for a given state.
    You would need to implement this based on your data source.
    Could be from a CSV, database, or API.
    """
    cities_df = pd.read_csv('us_cities.csv')
    return cities_df[cities_df['STATE_NAME'] == state]['CITY'].tolist()


def find_best_match(city: str, state: str, cache: LocationCache) -> Optional[str]:
    """
    Find the best matching city name using fuzzy matching.
    """
    # First check cache
    cached_correction = cache.get_correction(city, state)
    if cached_correction:
        logging.info(f"Found cached correction for {city}, {state} -> {cached_correction}")
        return cached_correction

    # Get list of valid cities for the state
    valid_cities = get_city_suggestions(state)

    best_match = None
    highest_ratio = 0

    # Find best fuzzy match
    for valid_city in valid_cities:
        ratio = fuzz.ratio(city.lower(), valid_city.lower())
        if ratio > highest_ratio and ratio > 80:  # 80% similarity threshold
            highest_ratio = ratio
            best_match = valid_city

    if best_match and best_match.lower() != city.lower():
        logging.info(f"Found fuzzy match: {city} -> {best_match} (similarity: {highest_ratio}%)")
        # Add to cache for future use
        cache.add_correction(city, best_match, state)
        return best_match

    return None


def geocode_with_fallback(station: str, trkname: str, county: str, state_str: str, cache: LocationCache) -> Optional[
    Dict]:
    """
    Attempt geocoding with multiple fallback strategies for finding rail yards.
    Station name correction is used only as a last resort.
    """
    logging.info(f"Attempting to geocode: {station}, {trkname}, {county}, {state_str}")

    def try_geocoding(queries: List[str]) -> Optional[Dict]:
        """Helper function to try geocoding with a list of queries"""
        for query in queries:
            logging.info(f"Trying query: {query}")
            results = geocode(query)
            railway_results = find_railway_matches(results)

            if railway_results:
                # Prioritize results that explicitly mention 'yard'
                sorted_results = sorted(
                    railway_results,
                    key=lambda x: ('yard' in str(x.get('properties', {})).lower()),
                    reverse=True
                )
                chosen = sorted_results[0]
                logging.info(f"Found match using query: {query}")
                return {
                    "longitude": chosen["longitude"],
                    "latitude": chosen["latitude"]
                }
        return None

    # Strategy 1: Try all variations with original station name
    queries = get_fallback_queries(station, trkname, county, state_str)
    result = try_geocoding(queries)
    if result:
        return result

    # Strategy 2: Try additional railway-specific terms
    railway_queries = [
        f"railway station {station}, {state_str}",
        f"railroad station {station}, {state_str}",
        f"train station {station}, {state_str}",
        f"{station} rail terminal, {state_str}",
        f"{station} railway terminal, {state_str}"
    ]
    result = try_geocoding(railway_queries)
    if result:
        return result

    # Strategy 3 (Last Resort): Try with corrected station name
    corrected_station = find_best_match(station, state_str, cache)
    if corrected_station and corrected_station != station:
        logging.info(f"Last resort - trying corrected station name: {station} -> {corrected_station}")

        # Try all variations with corrected station name
        corrected_queries = get_fallback_queries(corrected_station, trkname, county, state_str)
        corrected_queries.extend([
            f"railway station {corrected_station}, {state_str}",
            f"railroad station {corrected_station}, {state_str}",
            f"train station {corrected_station}, {state_str}",
            f"{corrected_station} rail terminal, {state_str}",
            f"{corrected_station} railway terminal, {state_str}"
        ])

        result = try_geocoding(corrected_queries)
        if result:
            return result

    logging.warning(f"Failed to find location for: {station}, {county}, {state_str}")
    return None


def validate_data(df: pd.DataFrame) -> None:
    """
    Validate and log information about the input data.
    """
    logging.info("\nData Validation:")

    # Check MILEPOST values
    milepost_counts = df['MILEPOST'].value_counts()
    logging.info(f"\nMILEPOST value counts:\n{milepost_counts}")

    # Check for YARD entries
    yard_mask = df['MILEPOST'].str.upper().str.strip() == 'YARD'
    yard_count = yard_mask.sum()
    logging.info(f"\nTotal YARD entries (case-insensitive): {yard_count}")

    # Check coordinate nulls
    coord_nulls = df[['Longitud', 'Latitude']].isna().sum()
    logging.info(f"\nNull coordinate counts:\n{coord_nulls}")

    # Find rows needing fixes
    needs_fix = df[
        (df['MILEPOST'].str.upper().str.strip() == 'YARD') &
        (df[['Longitud', 'Latitude']].isna().any(axis=1) |
         (df[['Longitud', 'Latitude']] == '').any(axis=1))
        ]
    logging.info(f"\nRows needing fixes: {len(needs_fix)}")

    if len(needs_fix) > 0:
        logging.info("\nSample of rows needing fixes:")
        sample = needs_fix.head(5)
        for idx, row in sample.iterrows():
            logging.info(f"""
            Row {idx}:
            MILEPOST: '{row.get('MILEPOST')}'
            Longitud: '{row.get('Longitud')}'
            Latitude: '{row.get('Latitude')}'
            STATION: '{row.get('STATION')}'
            STATE: '{row.get('STATE')}'
            """)


def fix_csv_geolocations(input_csv: str, output_csv: Optional[str] = None,
                        state_csv: str = "../../data/state_fips_master.csv") -> Optional[pd.DataFrame]:
    """
    Main function to process and fix geolocation data in the CSV.
    """
    try:
        # Initialize location cache
        cache = LocationCache()

        # Rest of the function remains the same, but pass cache to geocode_with_fallback
        df = pd.read_csv(input_csv, dtype=str)
        logging.info(f"Loaded {len(df)} rows from input CSV")

        validate_data(df)

        df_states = pd.read_csv(state_csv, dtype=str)
        fips_to_state = df_states.set_index("fips")["state_name"].to_dict()

        total_yard_rows = 0
        rows_needing_fix = 0
        rows_fixed = 0

        for idx, row in df.iterrows():
            if idx % 1000 == 0:
                logging.info(f"Processing row {idx}")

            milepost = str(row.get("MILEPOST", "")).strip().upper()
            longitud = str(row.get("Longitud", "")).strip()
            latitude = str(row.get("Latitude", "")).strip()

            if milepost == "YARD":
                total_yard_rows += 1

                if (not longitud or not latitude or
                        longitud.lower() == 'nan' or latitude.lower() == 'nan' or
                        longitud == '' or latitude == ''):

                    rows_needing_fix += 1
                    logging.debug(f"Row {idx} needs fixing")

                    station = str(row.get("STATION", "")).strip('" ')
                    trkname = str(row.get("TRKNAME", "")).strip('" ')
                    county = str(row.get("COUNTY", "")).strip('" ')
                    raw_state_code = str(row.get("STATE", "")).strip()

                    state_str = fips_to_state.get(raw_state_code, "")
                    # Pass cache to geocode_with_fallback
                    result = geocode_with_fallback(station, trkname, county, state_str, cache)

                    if result:
                        df.at[idx, "Longitud"] = result["longitude"]
                        df.at[idx, "Latitude"] = result["latitude"]
                        rows_fixed += 1
                        logging.info(f"Fixed row {idx}")

                    time.sleep(0.5)

        logging.info(f"""
        Summary:
        - Total rows processed: {len(df)}
        - Total YARD rows: {total_yard_rows}
        - Rows needing fixes: {rows_needing_fix}
        - Rows successfully fixed: {rows_fixed}
        - Success rate: {(rows_fixed / rows_needing_fix * 100) if rows_needing_fix > 0 else 0:.1f}%
        """)

        if output_csv:
            df.to_csv(output_csv, index=False)
            logging.info(f"Updated CSV written to {output_csv}")

        return df

    except Exception as e:
        logging.error(f"Fatal error in fix_csv_geolocations: {str(e)}")
        raise


if __name__ == "__main__":
    fix_csv_geolocations(
        input_csv='Railroad_Equipment_Accident_Incident.csv',
        output_csv='railroad_incidents_fixed.csv'
    )