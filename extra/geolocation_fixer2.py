import polars as pl
import logging, random

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='geocode_fix.log',
    filemode='w'
)

# This code only works with the mileposts and crossings dataset.
# Due to its size, it is not included in the git.

data = 'cleaned_incidents.csv'
names = 'combined_railroad.csv'
fix = 'railroad_incidents_fixed.csv'

mileposts = '../data/Rail_Mileposts_20241126.csv'
mileposts2 = 'Crossing_Inventory_Data__Form_71__-_Current_20241228.csv'
mileposts3 = 'Crossing_Inventory_Data__Form_71__-_Historical_20241228.csv'

df = pl.read_csv(data)
df_yard = pl.read_csv(fix)
mposts1 = pl.read_csv(mileposts)
mposts2 = pl.read_csv(mileposts2, ignore_errors=True)
mposts3 = pl.read_csv(mileposts3, ignore_errors=True)


missing = df_yard.filter(
    (pl.col('Latitude').is_null()) |
    (pl.col('Longitud').is_null()) |
    ((pl.col('Latitude') == 0) & (pl.col('Longitud') == 0))
)
size = missing.shape

updates = []       # Will store dicts of {INCDTNO, RAILROAD, MILEPOST, STCNTY, STATION, lat, lon}
success_count = 0  # Count how many times we actually found lat/lon

for i, entry in enumerate(missing.iter_rows(named=True)):
    percent = f"{(i / size[0] * 100):.1f}%"
    incident = entry['INCDTNO']
    railroad = entry['RAILROAD']
    milepost = entry['MILEPOST']
    stcnty_no_c = entry['STCNTY'].replace('C', '') if entry['STCNTY'] else None
    station = entry['STATION']

    if any(v is None for v in [milepost, stcnty_no_c]):
        logging.error(f"Row {i} has null milepost/STCNTY: {railroad}, {milepost}, {stcnty_no_c}, {station}")
        continue

    logging.info(f"Processing row {i} ({percent}) with {railroad}, {milepost}, {stcnty_no_c}, {station}")

    milepost_str = str(milepost)
    match_case = None

    # Determine whether the milepost is alphanumeric, float, integer, invalid
    if any(c.isalpha() for c in milepost_str):
        # 'alphanumeric'
        match_case = 'alphanumeric'
        prefix = ''.join(c for c in milepost_str if c.isalpha())
        milepost_str = ''.join(c for c in milepost_str if c.isdigit())
        logging.info(f"Split milepost {milepost} into prefix={prefix}, number={milepost_str}")
    else:
        prefix = None
        try:
            milepost_float = float(milepost_str)
            if float(milepost_float) == int(milepost_float):
                match_case = 'integer'
            else:
                match_case = 'float'
        except ValueError:
            match_case = 'invalid'

    lat, lon = None, None  # default if we don't find matches

    match match_case:
        case 'alphanumeric' | 'float':
            filter_conditions = [
                pl.col('Railroad Code').str.contains(railroad),
                pl.col("Railroad Milepost Number ").cast(pl.Utf8).str.contains(milepost_str),
                pl.col("County Code").cast(pl.Utf8) == stcnty_no_c,
                pl.col("Nearest Timetable Station ").str.contains(station, literal=True),
            ]
            if prefix:
                filter_conditions.append(
                    pl.col("Railroad Milepost Prefix ").cast(pl.Utf8) == prefix
                )

            combined_filter = filter_conditions[0]
            for condition in filter_conditions[1:]:
                combined_filter &= condition

            match_df = mposts2.filter(combined_filter)

            # If no match in mposts2, try mposts3
            if match_df.height == 0:
                logging.warning("No match in mposts2, trying mposts3...")
                from functools import reduce
                from operator import and_
                combined_filter = reduce(and_, filter_conditions)
                match_df = mposts3.filter(combined_filter)

            if match_df.height > 0:
                # If multiple matches, choose a random row
                if match_df.height > 1:
                    random_index = random.randint(0, match_df.height - 1)
                    logging.info(f"Found {match_df.height} matches, selecting row {random_index + 1}")
                    lat = match_df.get_column('Latitude')[random_index]
                    lon = match_df.get_column('Longitude')[random_index]
                else:
                    lat = match_df.get_column('Latitude')[0]
                    lon = match_df.get_column('Longitude')[0]

        case 'integer':
            match_df = mposts1.filter(
                (pl.col('RAILROAD').str.contains(railroad)) &
                (pl.col('MILEPOST').cast(pl.Utf8).str.contains(str(milepost))) &
                (pl.col('STCYFIPS').cast(pl.Utf8) == stcnty_no_c)
            )
            if match_df.height > 0:
                if match_df.height > 1:
                    # random selection if needed
                    idx = random.randint(0, match_df.height - 1)
                    lat = match_df.get_column('LAT')[idx]
                    lon = match_df.get_column('LONG')[idx]
                else:
                    lat = match_df.get_column('LAT')[0]
                    lon = match_df.get_column('LONG')[0]

        case 'invalid':
            logging.error(f"Invalid milepost format: {milepost}")
            continue

        case _:
            logging.error(f"Unexpected case for milepost: {milepost}")
            continue

    # If we found lat/lon, record success
    if lat is not None and lon is not None:
        logging.debug(f"Found {match_case} match: {lat}, {lon}")
        success_count += 1

        # stcnty needs the 'C' back in order to match the row in df_yard
        stcnty_full = f"C{stcnty_no_c}" if stcnty_no_c else None

        # Save the update info in a list
        updates.append({
            "INCDTNO": incident,
            "RAILROAD": railroad,
            "MILEPOST": milepost,
            "STCNTY": stcnty_full,
            "STATION": station,
            "Latitude_found": lat,
            "Longitud_found": lon
        })
    else:
        logging.warning(f"No {match_case} match found or lat/lon was null for row {i}")

# --- Done looping over missing rows ---

# Compute the success rate
total_missing = size[0]
success_rate = success_count / total_missing * 100 if total_missing > 0 else 0
logging.info(f"Success rate: {success_rate:.2f}%")

updates_df = pl.DataFrame(updates)
# Join on the unique keys that identify a row
df_yard_filled = (
    df_yard
    .join(
        updates_df,
        on=["INCDTNO", "RAILROAD", "MILEPOST", "STCNTY", "STATION"],
        how="left"
    )
    .with_columns([
        # Coalesce: if `Latitude` is null/0, fill from `Latitude_found`
        pl.col("Latitude").fill_null(pl.col("Latitude_found")).alias("Latitude"),
        pl.col("Longitud").fill_null(pl.col("Longitud_found")).alias("Longitud"),
    ])
    .drop(["Latitude_found", "Longitud_found"])
)

df_yard_filled.write_csv("railroad_incidents_fixed.csv")
logging.info("Wrote updated dataset to railroad_incidents_fixed.csv")