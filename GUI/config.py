from GUI.data import get_data

df, states_center, state_count, us_states, states_alphabetical, df_map = get_data()


date_min = df['corrected_year'].min()
date_max = df['corrected_year'].max()

attributes = df.columns

month_min = int(df['IMO'].min())
month_max = int(df['IMO'].max())

damage_min = df['ACCDMG'].min()
damage_max = 35000000

injuries_min = df['TOTINJ'].min()
injuries_max = 400

speed_min = df['TRNSPD'].min()
speed_max = df['TRNSPD'].max()

config = states_alphabetical

