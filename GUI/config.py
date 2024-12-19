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

config = [
    state for state in state_count['state_name']
]

