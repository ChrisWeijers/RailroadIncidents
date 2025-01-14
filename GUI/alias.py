from typing import Dict, List

aliases: Dict[str,str] = {
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
    'VISIBLTY': 'Visibility Code',
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

groups: Dict[str, List[str]] = {
    'Time': ['corrected_year', 'IMO', 'DATE'],
    'Incident Details': ['TYPE', 'CARS', 'CARSDMG', 'CARSHZD', 'EVACUATE'],
    'Environmental': ['TEMP', 'VISIBLTY', 'WEATHER'],
    'Train Details': [
        'TRNSPD', 'TONS',
        'LOADF1', 'LOADP1', 'EMPTYF1', 'EMPTYP1',
        'LOADF2', 'LOADP2', 'EMPTYF2', 'EMPTYP2'
    ],
    'Damage Information': ['ACCDMG', 'EQPDMG', 'TRKDMG'],
    'Personnel': ['TOTINJ', 'TOTKLD', 'ENGRS', 'FIREMEN', 'CONDUCTR', 'BRAKEMEN'],
    'Safety': ['ALCOHOL', 'DRUG']
}

ATTRIBUTE_TYPES: Dict[str,str] = {
    "corrected_year": "Ordered Quantitative",
    "IMO": "Ordered Cyclic",
    "RAILROAD": "Categorical",
    'TYPE': 'Categorical',
    "CARS": "Ordered Quantitative",
    "CARSDMG": "Ordered Quantitative",
    "CARSHZD": "Ordered Quantitative",
    "EVACUATE": "Ordered Quantitative",
    "TEMP": "Ordered Quantitative",
    "VISIBLTY": "Ordered Sequential",
    "WEATHER": "Categorical",
    "TRNSPD": "Ordered Quantitative",
    "TONS": "Ordered Quantitative",
    "LOADF1": "Ordered Quantitative",
    "LOADP1": "Ordered Quantitative",
    "EMPTYF1": "Ordered Quantitative",
    "EMPTYP1": "Ordered Quantitative",
    "LOADF2": "Ordered Quantitative",
    "LOADP2": "Ordered Quantitative",
    "EMPTYF2": "Ordered Quantitative",
    "EMPTYP2": "Ordered Quantitative",
    "ACCDMG": "Ordered Quantitative",
    "EQPDMG": "Ordered Quantitative",
    "TRKDMG": "Ordered Quantitative",
    "TOTINJ": "Ordered Quantitative",
    "TOTKLD": "Ordered Quantitative",
    "ENGRS": "Ordered Quantitative",
    "FIREMEN": "Ordered Quantitative",
    "CONDUCTR": "Ordered Quantitative",
    "BRAKEMEN": "Ordered Quantitative",
    "ALCOHOL": "Ordered Quantitative",
    "DRUG": "Ordered Quantitative",
}

# Compatible visualizations for each attribute type
COMPATIBLE_VIZ: Dict[str, List[str]] = {
    "Categorical": ["grouped_bar"],
    "Ordered Quantitative": [
        "scatter",
        "scatter_size",
        "scatter_trendline",
        "boxplot",
    ],
    "Ordered Sequential": [
        "clustered_bar",
    ],
    "Ordered Cyclic": ["scatter_trendline"],
}

# Compatible attribute types for comparisons
COMPATIBLE_TYPES: Dict[str, List[str]] = {
    "Categorical": ["Categorical", "Ordered Quantitative"],
    "Ordered Quantitative": ["Ordered Quantitative", "Categorical"],
    "Ordered Sequential": ["Ordered Sequential", "Ordered Quantitative"],
    "Ordered Cyclic": ["Ordered Cyclic", "Ordered Quantitative"],
}


incident_types: Dict[str, str] = {
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

visibility: Dict[int, str] = {
    1: 'Dawn',
    2: 'Day',
    3: 'Dusk',
    4: 'Dark',
}

weather: Dict[int, str] = {
    1: 'Clear',
    2: 'Cloudy',
    3: 'Rain',
    4: 'Fog',
    5: 'Sleet',
    6: 'Snow',
}

def create_grouped_options(attributes: List[str], aliases: Dict[str, str]) -> List[Dict[str, str]]:
    """Create options with grouped structure for first dropdown."""
    options = []
    for group_name, group_attributes in groups.items():
        valid_attributes = [attr for attr in group_attributes
                          if attr in attributes]
        if valid_attributes:
            for attr in valid_attributes:
                if attr in aliases:
                    options.append({
                        'label': f"{group_name} - {aliases[attr]}",
                        'value': attr
                    })
    return options

def create_comparison_options(attributes: List[str], aliases: Dict[str, str],
                            attr_type: str, selected_attr: str) -> List[Dict[str, str]]:
    """Create comparison options with grouped structure."""
    options = []
    for group_name, group_attributes in groups.items():
        valid_attributes = [
            attr for attr in group_attributes
            if (attr in ATTRIBUTE_TYPES and
                ATTRIBUTE_TYPES[attr] in COMPATIBLE_TYPES.get(attr_type, []) and
                attr != selected_attr)
        ]
        if valid_attributes:
            for attr in valid_attributes:
                if attr in aliases:
                    options.append({
                        'label': f"{group_name} - {aliases[attr]}",
                        'value': attr
                    })
    return options