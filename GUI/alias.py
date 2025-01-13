from typing import Dict

aliases: Dict = {
    'corrected_year': 'Incident Year',
    'IMO': 'Incident Month',
    'DATE': 'Incident Date',
    'RAILROAD': 'Reporting Railroad Code',
    'TYPE': 'Type of Incident',
    'CARS': 'Hazmat Cars Involved',
    'CARSDMG': 'Hazmat Cars Damaged/Derailed',
    'CARSHZD': 'Hazmat Cars Released',
    'EVACUATE': 'Persons Evacuated',
    'TEMP': 'Temperature',
    'VISIBILITY': 'Visibility Code',
    'WEATHER': 'Weather Condition Code',
    'TRNSPD': 'Train Speed (mph)',
    'TONS': 'Trailing Tons',
    'LOADF1': 'Loaded Freight Cars',
    'LOADP1': 'Loaded Passenger Cars',
    'EMPTYF1': 'Empty Freight Cars',
    'EMPTYP1': 'Empty Passenger Cars',
    'LOADF2': 'Derailed Loaded Freight Cars',
    'LOADP2': 'Derailed Loaded Passenger Cars',
    'EMPTYF2': 'Derailed Empty Freight Cars',
    'EMPTYP2': 'Derailed Empty Passenger Cars',
    'ACCDMG': 'Total Damage Cost',
    'EQPDMG': 'Equipment Damage Cost',
    'TRKDMG': 'Track Damage Cost',
    'TOTINJ': 'Total Injuries',
    'TOTKLD': 'Total Fatalities',
    'ENGRS': 'Engineers on Duty',
    'FIREMEN': 'Firemen on Duty',
    'CONDUCTR': 'Conductors on Duty',
    'BRAKEMEN': 'Brakemen on Duty',
    'ALCOHOL': 'Positive Alcohol Tests',
    'DRUG': 'Positive Drug Tests',
}

incident_types: Dict = {
    '01': 'Derailment',
    '02': 'Head on collision',
    '03': 'Rearend collision',
    '04': 'Side collision',
    '05': 'Raking collision',
    '06': 'Broken train collision',
    '07': 'Hwy-rail crossing',
    '08': 'RR Grade Crossing',
    '09': 'Obstruction',
    '10': 'Explosive-detonation',
    '11': 'Fire/Violent rupture',
    '12': 'Other impacts',
    '13': 'Other (described in narration)'
}

visibility: Dict = {
    1: 'Dawn',
    2: 'Day',
    3: 'Dusk',
    4: 'Dark',
}

weather: Dict = {
    1: 'Clear',
    2: 'Cloudy',
    3: 'Rain',
    4: 'Fog',
    5: 'Sleet',
    6: 'Snow',
}