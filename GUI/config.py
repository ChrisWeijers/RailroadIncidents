from GUI.data import get_data

df, states_center, state_count, us_states = get_data()


year_min = 2000
year_max = int(df['corrected_year'].max())

month_min = int(df['IMO'].min())
month_max = int(df['IMO'].max())

damage_min = df['ACCDMG'].min()
damage_max = 35000000

injuries_min = df['TOTINJ'].min()
injuries_max = 400

speed_min = df['TRNSPD'].min()
speed_max = df['TRNSPD'].max()

config = {
    'year_min': year_min,
    'year_max': year_max,
    'month_min': month_min,
    'month_max': month_max,
    'damage_min': damage_min,
    'damage_max': damage_max,
    'injuries_min': injuries_min,
    'injuries_max': injuries_max,
    'speed_min': speed_min,
    'speed_max': speed_max,
}