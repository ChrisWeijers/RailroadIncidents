from typing import Dict
from GUI.data import get_data
from shapely.geometry import Polygon

# Load data
df, states_center, state_count, us_states, states_alphabetical, city_data, crossing_data = get_data()

# Create aliased dictionary
aliases: Dict[str, str] = {
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

# Create list of dictionary for the labels of plots in the dropdown
viz_options = [
    # ----- (1) Analyzing Temporal Trends -----
    {
        "label": "Time Trend - Total incidents timeline (Line Chart)",
        "value": "plot_1_1",
    },
    {
        "label": "Time Trend - Incident types trends (Stream Graph)",
        "value": "plot_1_2",
    },
    {
        "label": "Time Trend - Seasonal analysis (Heat Map)",
        "value": "plot_1_3",
    },
    # ----- (2) Geographic Detail -----
    {
        "label": "Geographic Detail - Type Of Incident Per State (Sunburst Chart)",
        "value": "plot_2_1",
    },
    # ----- (3) Contributing Factors -----
    {
        "label": "Contributing Factor - Damage Distribution With Multiple Factors (Parallel Coordinate Plot)",
        "value": "plot_2_3",
    },
    {
        "label": "Contributing Factor - Severity Impact (Heat Map)",
        "value": "plot_3_2",
    },
    {
        "label": "Contributing Factor - Common Combinations (Stacked Bar Chart)",
        "value": "plot_3_3",
    },
    # ----- (4) Operator Performance -----
    {
        "label": "Operator Performance - Incident Rate Comparison (Bar Chart)",
        "value": "plot_4_1",
    },
    {
        "label": "Operator Performance - Type Distribution (Grouped Bar Chart)",
        "value": "plot_4_2",
    },
    {
        "label": "Operator Performance - Incident Type Rankings (Violin Plot)",
        "value": "plot_4_3",
    },
    # ----- (5) High-Impact Incidents -----
    {
        "label": "High Impact - Incident Codes (Sunburst Chart)",
        "value": "plot_5_2",
    },
    # ----- (6) Summarizing Incident Characteristics -----
    {
        "label": "Incident Characteristics - Most Common Types (Stacked Bar Chart)",
        "value": "plot_6_1",
    },
    {
        "label": "Incident Characteristics - Damage Cost Analysis (Violin Plot)",
        "value": "plot_6_3",
    },
]

# Create dictionary with the incident type numbers and their belonging description
incident_types: Dict[int, str] = {
    1: 'Derailment',
    2: 'Head on collision',
    3: 'Rearend collision',
    4: 'Side collision',
    5: 'Raking collision',
    6: 'Broken train collision',
    7: 'Hwy-rail crossing',
    8: 'RR Grade Crossing',
    9: 'Obstruction',
    10: 'Explosive-detonation',
    11: 'Fire/Violent rupture',
    12: 'Other impacts',
    13: 'Other (described in narration)'
}

# Create dictionary with the visibility numbers and their belonging description
visibility: Dict[int, str] = {
    1: 'Dawn',
    2: 'Day',
    3: 'Dusk',
    4: 'Dark',
}

# Create dictionary with the weather numbers and their belonging description
weather: Dict[int, str] = {
    1: 'Clear',
    2: 'Cloudy',
    3: 'Rain',
    4: 'Fog',
    5: 'Sleet',
    6: 'Snow',
}

# Create dictionary with the cause codes and belonging description and types
fra_cause_codes = {
    "TRACK, ROADBED AND STRUCTURES": {
        "Roadbed": {
            "T001": "Roadbed settled or soft",
            "T002": "Washout/rain/slide/flood/snow/ice damage to track",
            "T099": "Other roadbed defects (Provide detailed description in narrative)"
        },
        "Track Geometry": {
            "T101": "Cross level of track irregular (at joints)",
            "T102": "Cross level of track irregular (not at joints)",
            "T103": "Deviation from uniform top of rail profile",
            "T104": "Disturbed ballast section",
            "T105": "Insufficient ballast section",
            "T106": "Superelevation improper, excessive, or insufficient",
            "T107": "Superelevation runoff improper",
            "T108": "Track alignment irregular (other than buckled/sunkink)",
            "T109": "Track alignment irregular (buckled/sunkink)",
            "T110": "Wide gage (due to defective or missing crossties)",
            "T111": "Wide gage (due to defective or missing spikes or other rail fasteners)",
            "T112": "Wide gage (due to loose, broken, or defective gage rods)",
            "T113": "Wide gage (due to worn rails)",
            "T199": "Other track geometry defects (Provide detailed description in narrative)"
        },
        "Rail, Joint Bar and Rail Anchoring": {
            "T201": "Broken Rail - Bolt hole crack or break",
            "T202": "Broken Rail - Base",
            "T203": "Broken Rail - Weld (plant)",
            "T204": "Broken Rail - Weld (field)",
            "T205": "Defective or missing crossties (use code T110 if results in wide gage)",
            "T206": "Defective spikes or missing spikes or other rail fasteners (use code T111 if results in wide gage)",
            "T207": "Broken Rail - Detail fracture from shelling or head check",
            "T208": "Broken Rail - Engine burn fracture",
            "T210": "Broken Rail - Head and web separation (outside joint bar limits)",
            "T211": "Broken Rail - Head and web separation (within joint bar limits)",
            "T212": "Broken Rail - Horizontal split head",
            "T213": "Joint bar broken (compromise)",
            "T214": "Joint bar broken (insulated)",
            "T215": "Joint bar broken (noninsulated)",
            "T216": "Joint bolts, broken, or missing",
            "T217": "Mismatched rail-head contour",
            "T218": "Broken Rail - Piped rail",
            "T219": "Rail defect with joint bar repair",
            "T220": "Broken Rail - Transverse/compound fissure",
            "T221": "Broken Rail - Vertical split head",
            "T222": "Worn rail",
            "T223": "Rail Condition - Dry rail, freshly ground rail",
            "T299": "Other rail and joint bar defects (Provide detailed description in narrative)"
        }
    },
    "SIGNAL AND COMMUNICATION": {
        "S001": "Automatic cab signal displayed false proceed",
        "S002": "Automatic cab signal inoperative",
        "S003": "Automatic train control system inoperative",
        "S004": "Automatic train-stop device inoperative",
        "S005": "Block signal displayed false proceed",
        "S006": "Classification yard automatic control system switch failure",
        "S007": "Classification yard automatic control system retarder failure",
        "S008": "Fixed signal improperly displayed (defective)",
        "S009": "Interlocking signal displayed false proceed",
        "S010": "Power device interlocking failure",
        "S011": "Power switch failure",
        "S012": "Radio communication equipment failure",
        "S013": "Other communication equipment failure",
        "S014": "Computer system design error (vendor)",
        "S015": "Computer system configuration/management error (vendor)",
        "S016": "Classification yard automatic control system - Inadequate or insufficient control",
        "S099": "Other signal failures (Provide detailed description in narrative)",
        "S101": "Remote control transmitter defective",
        "S102": "Remote control transmitter, loss of communication",
        "S103": "Radio controlled switch communication failure",
        "S104": "Radio controlled switch not locked effectively"
    },
    "MECHANICAL AND ELECTRICAL FAILURES": {
        "Brakes": {
            "E00C": "Air hose uncoupled or burst",
            "E00L": "Air hose uncoupled or burst (LOCOMOTIVE)",
            "E01C": "Hydraulic hose uncoupled or burst",
            "E01L": "Hydraulic hose uncoupled or burst (LOCOMOTIVE)",
            "E02C": "Broken brake pipe or connections",
            "E02L": "Broken brake pipe or connections (LOCOMOTIVE)",
            "E03C": "Obstructed brake pipe (closed angle cock, ice, etc.)",
            "E03L": "Obstructed brake pipe (closed angle cock, ice, etc.) (LOCOMOTIVE)",
            "E04C": "Other brake components damaged, worn, broken, or disconnected",
            "E04L": "Other brake components damaged, worn, broken, or disconnected (LOCOMOTIVE)",
            "E05C": "Brake valve malfunction (undesired emergency)",
            "E05L": "Brake valve malfunction (undesired emergency) (LOCOMOTIVE)",
            "E06C": "Brake valve malfunction (stuck brake, etc.)",
            "E06L": "Brake valve malfunction (stuck brake, etc.) (LOCOMOTIVE)",
            "E07C": "Rigging down or dragging",
            "E07L": "Rigging down or dragging (LOCOMOTIVE)",
            "E08C": "Hand brake (including gear) broken or defective",
            "E08L": "Hand brake (including gear) broken or defective (LOCOMOTIVE)",
            "E0HC": "Hand brake linkage and/or connections broken or defective",
            "E0HL": "Hand brake linkage/Connections broken/defective (LOCOMOTIVE)",
            "E09C": "Other brake defects, cars (Provide detailed description in narrative)",
            "E09L": "Other brake defects, (Provide detailed description in narrative) (LOCOMOTIVE)",
            "E10L": "Computer controlled brake communication failure (LOCOMOTIVE)"
        },
        "Trailer Or Container On Flatcar": {
            "E11C": "Broken or defective tiedown equipment",
            "E12C": "Broken or defective container",
            "E13C": "Broken or defective trailer",
            "E19C": "Other trailer or container on flat car defects (Provide detailed description in narrative)"
        },
        "Body": {
            "E20C": "Body bolster broken or defective",
            "E20L": "Body bolster broken or defective (LOCOMOTIVE)",
            "E21C": "Center sill broken or bent",
            "E21L": "Center sill broken or bent (LOCOMOTIVE)",
            "E22C": "Draft sill broken or bent",
            "E22L": "Draft sill broken or bent (LOCOMOTIVE)",
            "E23C": "Center plate broken or defective",
            "E23L": "Center plate broken or defective (LOCOMOTIVE)",
            "E24C": "Center plate disengaged from truck (car off center)",
            "E24L": "Center plate disengaged from truck unit/off center (LOCOMOTIVE)",
            "E25C": "Center pin broken or missing",
            "E25L": "Center pin broken or missing (LOCOMOTIVE)",
            "E26C": "Center plate attachment defective",
            "E26L": "Center plate attachment defective (LOCOMOTIVE)",
            "E27C": "Side sill broken",
            "E27L": "Side sill broken (LOCOMOTIVE)",
            "E29C": "Other body defects, (CAR) (Provide detailed description in narrative)",
            "E29L": "Other body defects, (LOCOMOTIVE) (Provide detailed description in narrative)"
        },
        "Coupler and Draft System": {
            "E30C": "Knuckle broken or defective",
            "E30L": "Knuckle broken or defective (LOCOMOTIVE)",
            "E31C": "Coupler mismatch, high/low",
            "E31L": "Coupler mismatch, high/low (LOCOMOTIVE)",
            "E32C": "Coupler drawhead broken or defective",
            "E32L": "Coupler drawhead broken or defective (LOCOMOTIVE)",
            "E33C": "Coupler retainer pin/cross key missing",
            "E33L": "Coupler retainer pin/cross key missing (LOCOMOTIVE)",
            "E34C": "Draft gear/mechanism broken or defective (including yoke)",
            "E34L": "Draft gear/mechanism broken/defective (including yoke) (LOCOMOTIVE)",
            "E35C": "Coupler carrier broken or defective",
            "E35L": "Coupler carrier broken or defective (LOCOMOTIVE)",
            "E36C": "Coupler shank broken or defective (includes defective alignment control)",
            "E36L": "Coupler shank broken or defective (includes defective includes defective alignment control) (LOCOMOTIVE)",
            "E37C": "Failure of articulated connectors",
            "E37L": "Failure of articulated connectors (LOCOMOTIVE)",
            "E39C": "Other coupler and draft system defects, (CAR) (Provide detailed description in narrative)",
            "E39L": "Other coupler and draft system defects, (LOCOMOTIVE) (Provide detailed description in narrative)"
        },
        "Truck Components": {
            "E40C": "Side bearing clearance insufficient",
            "E40L": "Side bearing clearance insufficient (LOCOMOTIVE)",
            "E41C": "Side bearing clearance excessive",
            "E41L": "Side bearing clearance excessive (LOCOMOTIVE)",
            "E42C": "Side bearing(s) broken",
            "E42L": "Side bearing(s) broken (LOCOMOTIVE)",
            "E43C": "Side bearing(s) missing",
            "E43L": "Side bearing(s) missing (LOCOMOTIVE)",
            "E44C": "Truck bolster broken",
            "E44L": "Truck bolster broken (LOCOMOTIVE)",
            "E45C": "Side frame broken",
            "E45L": "Side frame broken (LOCOMOTIVE)",
            "E46C": "Truck bolster stiff, improper swiveling",
            "E4AC": "Gib Clearance (lateral motion excessive)",
            "E4BC": "Truck bolster stiff (failure to slew)",
            "E46L": "Truck bolster stiff, improper lateral or improper swiveling(LOCOMOTIVE)",
            "E47C": "Defective snubbing (including friction and hydraulic)",
            "E47L": "Defective snubbing (LOCOMOTIVE)",
            "E48C": "Broken, missing, or otherwise defective springs (including incorrect repair and/or installation)",
            "E48L": "Broken, missing, or otherwise defective springs (LOCOMOTIVE)",
            "E4TC": "Truck hunting",
            "E4TL": "Truck hunting (LOCOMOTIVE)",
            "E49C": "Other truck component defects, including mismatched side frames (CAR) (Provide detailed description in narrative)",
            "E49L": "Other truck component defects, (LOCOMOTIVE) (Provide detailed description in narrative)"
        },
        "Axles and Journal Bearings": {
            "E51C": "Broken or bent axle between wheel seats",
            "E51L": "Broken or bent axle between wheel seats (LOCOMOTIVE)",
            "E52C": "Journal (plain) failure from overheating",
            "E52L": "Journal (plain) failure from overheating (LOCOMOTIVE)",
            "E53C": "Journal (roller bearing) failure from overheating",
            "E53L": "Journal (roller bearing) failure from overheating- LOCOMOTIVE",
            "E54C": "Journal fractured, new cold break",
            "E54L": "Journal fractured, new cold break (LOCOMOTIVE)",
            "E55C": "Journal fractured, cold break, previously overheated",
            "E55L": "Journal fractured, cold break, previously overheated (LOCOMOTIVE)",
            "E59C": "Other axle and journal bearing defects (CAR) (Provide detailed description in narrative)",
            "E59L": "Other axle and journal bearing defects (LOCOMOTIVE) (Provide detailed description in narrative)"
        },
        "Wheels": {
            "E60C": "Broken flange",
            "E60L": "Broken flange (LOCOMOTIVE)",
            "E61C": "Broken rim",
            "E61L": "Broken rim (LOCOMOTIVE)",
            "E62C": "Broken plate",
            "E62L": "Broken plate (LOCOMOTIVE)",
            "E63C": "Broken hub",
            "E63L": "Broken hub (LOCOMOTIVE)",
            "E64C": "Worn flange",
            "E64L": "Worn flange (LOCOMOTIVE)",
            "E65C": "Worn tread",
            "E65L": "Worn tread (LOCOMOTIVE)",
            "E66C": "Damaged flange or tread (flat)",
            "E66L": "Damaged flange or tread (flat) (LOCOMOTIVE)",
            "E67C": "Damaged flange or tread (build up)",
            "E67L": "Damaged flange or tread (build up) (LOCOMOTIVE)",
            "E68C": "Loose wheel",
            "E68L": "Loose wheel (LOCOMOTIVE)",
            "E6AC": "Thermal crack, flange or tread",
            "E6AL": "Thermal crack, flange or tread (LOCOMOTIVE)",
            "E69C": "Other wheel defects (CAR) (Provide detailed description in narrative)",
            "E69L": "Other wheel defects (LOCOMOTIVE) (Provide detailed description in narrative)"
        },
        "Locomotives": {
            "E70L": "Running gear failure (LOCOMOTIVE)",
            "E71L": "Traction motor failure (LOCOMOTIVE)",
            "E72L": "Crank case or air box explosion (LOCOMOTIVE)",
            "E73L": "Oil or fuel fire (LOCOMOTIVE)",
            "E74L": "Electrically caused fire (LOCOMOTIVE)",
            "E75L": "Current collector system (LOCOMOTIVE)",
            "E76L": "Remote control equipment inoperative (LOCOMOTIVE)",
            "E77L": "Broken or defective swing hanger or spring plank (LOCOMOTIVE)",
            "E78L": "Pantograph defect (LOCOMOTIVE)",
            "E7AL": "On-board computer - failure to respond (LOCOMOTIVE)",
            "E7BL": "Third rail shoe or shoe beam (LOCOMOTIVE)",
            "E79L": "Other locomotive defects (Provide detail description in narrative)"
        },
        "Doors": {
            "E80C": "Box car plug door open",
            "E81C": "Box car plug door, attachment defective",
            "E82C": "Box car plug door, locking lever not in place",
            "E83C": "Box car door, other than plug, open",
            "E84C": "Box car door, other than plug, attachment defective",
            "E85C": "Bottom outlet car door open",
            "E86C": "Bottom outlet car door attachment defective",
            "E89C": "Other car door defects (Provide detailed description in narrative)",
            "E99C": "Other mechanical and electrical failures, (CAR) (Provide detailed description in narrative)",
            "E99L": "Other mechanical and electrical failures, (LOCOMOTIVE) (Provide detailed description in narrative)",
        }
    },
    "TRAIN OPERATION - HUMAN FACTORS": {
        "Brakes, Use of": {
            "H008": "Improper operation of train line air connections (bottling the air)",
            "H017": "Failure to properly secure engine(s) (railroad employee)",
            "H018": "Failure to properly secure hand brake on car(s) (railroad employee)",
            "H019": "Failure to release hand brakes on car(s) (railroad employee)",
            "H020": "Failure to apply sufficient number of hand brakes on car(s) (railroad employee)",
            "H021": "Failure to apply hand brakes on car(s) (railroad employee)",
            "H022": "Failure to properly secure engine(s) or car(s) (non railroad employee)",
            "H025": "Failure to control speed of car using hand brake (railroad employee)",
            "H099": "Use of brakes, other (Provide detailed description in narrative)"
        },
        "Employee Physical Condition": {
            "H101": "Impairment of efficiency or judgment because of drugs or alcohol",
            "H102": "Incapacitation due to injury or illness",
            "H103": "Employee restricted in work or motion",
            "H104": "Employee asleep",
            "H199": "Employee physical condition, other (Provide detailed description in narrative)"
        },
        "Flagging, Fixed, Hand and Radio Signals": {
            "H201": "Blue Signal, absence of",
            "H202": "Blue Signal, imperfectly displayed",
            "H205": "Flagging, improper or failure to flag",
            "H206": "Flagging signal, failure to comply",
            "H207": "Hand signal, failure to comply",
            "H208": "Hand signal improper",
            "H209": "Hand signal, failure to give/receive",
            "H210": "Radio communication, failure to comply",
            "H211": "Radio communication, improper",
            "H212": "Radio communication, failure to give/receive",
            "H213": "Automatic cab signal failure to convey a visible inspection of moving train",
            "H214": "Automatic cab signal, improperly displayed (improperly spaced train inspection rules)",
            "H215": "Automatic cab signal, false proceed indication - failure to comply",
            "H216": "Automatic cab signal, improperly displayed",
            "H217": "Automatic cab signal, false proceed indication - failure to comply"
        },
        "General Switching Rules": {
            "H301": "Car(s) shoved out and left out of clear",
            "H302": "Cars left foul",
            "H303": "Derail, failure to apply or remove",
            "H304": "Hazardous materials regulations, failure to comply",
            "H305": "Instruction to train/yard crew improper",
            "H306": "Shoving movement, absence of man on or at leading end of movement",
            "H307": "Shoving movement, man on or at leading end of movement, failure to control",
            "H308": "Skate, failure to remove or place",
            "H309": "Failure to stretch cars before shoving",
            "H310": "Failure to couple",
            "H311": "Moving cars while loading ramp/hose/chute/cables/bridge plate, etc., not in proper position",
            "H312": "Passed couplers (other than automated classification yard)",
            "H313": "Retarder, improper manual operation",
            "H314": "Retarder yard skate improperly applied",
            "H315": "Portable derail, improperly applied",
            "H316": "Manual intervention of classification yard automatic control system modes by operator",
            "H317": "Humping or cutting off in motion equipment susceptible to damage, or to cause damage to other equipment",
            "H318": "Kicking or dropping cars, inadequate precautions",
            "H399": "Other general switching rules (Provide detailed description in narrative)"
        },
        "Main Track Authority": {
            "H401": "Failure to stop train in clear",
            "H402": "Motor car or on-track equipment rules, failure to comply",
            "H403": "Movement of engine(s) or car(s) without authority (railroad employee)",
            "H404": "Train order, track warrant, track bulletin, or timetable authority, failure to comply",
            "H405": "Train orders, track warrants, direct traffic control, track bulletins, radio, error in preparation, transmission",
            "H406": "Train orders, track warrants, direct traffic control, track bulletins, written, error in preparation, transmission or delivery",
            "H499": "Other main track authority causes (Provide detailed description in narrative)"
        },
        "Train Handling/Train Make-Up": {
            "H501": "Improper train make-up at initial terminal",
            "H502": "Improper placement of cars in train between terminals",
            "H503": "Buffing or slack action: excessive, train handling",
            "H504": "Buffing or slack action excessive, train make-up",
            "H505": "Lateral drawbar force on curve excessive, train handling",
            "H506": "Lateral drawbar force on curve excessive, train make-up",
            "H507": "Lateral drawbar force on curve excessive, car geometry (short car/long car combination)",
            "H508": "Improper train make-up",
            "H509": "Improper train inspection",
            "H510": "Automatic brake, insufficient (H001) – see note after cause H599",
            "H511": "Automatic brake, excessive (H002)",
            "H512": "Automatic brake, failure to use split reduction (H003)",
            "H513": "Automatic brake, other improper use (H004)",
            "H514": "Failure to allow air brakes to fully release before proceeding (H005)",
            "H515": "Failure to properly cut-out brake valves on locomotives (H006)",
            "H516": "Failure to properly cut-in brake valves on locomotives (H007)",
            "H517": "Dynamic brake, insufficient (H009)",
            "H518": "Dynamic brake, excessive (H010)",
            "H519": "Dynamic brake, too rapid adjustment (H011)",
            "H520": "Dynamic brake, excessive axles (H012)",
            "H521": "Dynamic brake, other improper use (H013)",
            "H522": "Throttle (power), improper use (H014)",
            "H523": "Throttle (power), too rapid adjustment (H015)",
            "H524": "Excessive horsepower (H016)",
            "H525": "Independent (engine) brake, improper use (except actuation) (H023)",
            "H526": "Failure to actuate off independent brake (H024)",
            "H599": "Other causes relating to train handling or makeup (Provide detailed description in narrative)"
        },
        "Speed": {
            "H601": "Coupling speed excessive",
            "H602": "Switching movement, excessive speed",
            "H603": "Train on main track inside yard limits, excessive speed",
            "H604": "Train outside yard limits, in block signal or interlocking territory, excessive speed",
            "H605": "Failure to comply with restricted speed in connection with the restrictive indication of a block or interlocking signal",
            "H606": "Train outside yard limits in nonblock territory, excessive speed",
            "H607": "Failure to comply with restricted speed or its equivalent not in connection with a block or interlocking signal",
            "H699": "Speed, other (Provide detailed description in narrative)"
        },
        "Miscellaneous": {
            "H991": "Tampering with safety/protective device(s)",
            "H992": "Operation of locomotive by uncertified/unqualified person",
            "H993": "Human Factor - track",
            "H994": "Human Factor - Signal installation or maintenance error (field)",
            "H99A": "Human Factor - Signal - Train Control - Installation or maintenance error (shop)",
            "H99B": "Human Factor - Signal - Train Control - Operator Input On-board computer incorrect data entry",
            "H99C": "Human Factor - Signal - Train Control - Operator Input On-board computer incorrect data provided",
            "H99D": "Computer system design error (non vendor)",
            "H99E": "Computer system configuration/management error (non vendor)",
            "H995": "Human Factor - motive power and equipment",
            "H996": "Oversized loads or Excess Height/Width cars, mis-routed or switched",
            "H997": "Motor car or other on-track equipment rules (other than main track authority) - Failure to Comply",
            "H999": "Other train operation/human factors (Provide detailed description in narrative)"
        }
    },
    "MISCELLANEOUS CAUSES NOT OTHERWISE LISTED": {
        "Environmental Conditions": {
            "M101": "Snow, ice, mud, gravel, coal, sand, etc. on track",
            "M102": "Extreme environmental condition - TORNADO",
            "M103": "Extreme environmental condition - FLOOD",
            "M104": "Extreme environmental condition - DENSE FOG",
            "M105": "Extreme environmental condition - EXTREME WIND VELOCITY",
            "M199": "Other extreme environmental conditions (Provide detailed description in narrative)"
        },
        "Loading Procedures": {
            "M201": "Load shifted",
            "M202": "Load fell from car",
            "M203": "Overloaded car",
            "M204": "Improperly loaded car",
            "M206": "Trailer or container tiedown equipment: improperly applied",
            "M207": "Overloaded container/trailer on flat car",
            "M208": "Improperly loaded container/trailer on flat car",
            "M299": "Miscellaneous loading procedures (Provide detailed description in narrative)"
        },
        "Highway-Rail Grade Crossing Accidents": {
            "M301": "Highway user impairment because of drug or alcohol usage (as determined by local authorities, e.g., police)",
            "M302": "Highway user inattentiveness",
            "M303": "Highway user misjudgment under normal weather and traffic conditions",
            "M304": "Highway user cited for violation of highway-rail grade crossing traffic laws",
            "M305": "Highway user unawareness due to environmental factors (angle of sun, etc.)",
            "M306": "Highway user inability to stop due to extreme weather conditions (dense fog, ice, or snow packed road, etc.)",
            "M307": "Malfunction, improper operation of train activated warning devices",
            "M308": "Highway user deliberately disregarded crossing warning devices",
            "M399": "Other causes (Provide detailed description in narrative)"
        },
        "Unusual Operational Situations": {
            "M401": "Emergency brake application to avoid accident",
            "M402": "Object or equipment on or fouling track (motor vehicle - other than highway-rail crossing)",
            "M403": "Object or equipment on or fouling track (livestock)",
            "M404": "Object or equipment on or fouling track - other than above (for vandalism, see code M503)",
            "M405": "Interaction of lateral/vertical forces (includes harmonic rock off)",
            "M406": "Fire, other than vandalism, involving on-track equipment"
        },
        "Other Miscellaneous": {
            "M407": "Automatic hump retarder failed to sufficiently slow car due to foreign material on wheels of car being humped",
            "M408": "Yard skate slid and failed to stop cars",
            "M409": "Objects such as lading chains or straps fouling switches",
            "M410": "Objects such as lading chains or straps fouling wheels",
            "M411": "Passed couplers (automated classification yard)",
            "M501": "Interference (other than vandalism) with railroad operations by nonrailroad employee",
            "M502": "Vandalism of on-track equipment, e.g., brakes released",
            "M503": "Vandalism of track or track appliances, e.g., objects placed on track, switch thrown, etc.",
            "M504": "Failure by nonrailroad employee, e.g., industry employee, to control speed of car using hand brake",
            "M505": "Cause under active investigation by reporting railroad (Amended report will be forwarded when reporting railroad’s active investigation has been completed.)",
            "M506": "Track damage caused by non-railroad interference with track structure",
            "M507": "Investigation complete, cause could not be determined (When using this code, the narrative must include the reason(s) why the cause of the accident/incident could not be determined.)",
            "M599": "Other miscellaneous causes (Provide detailed description in narrative)"
        },
    }
}


# Flatten fra_cause_codes to map detailed codes to their categories
def generate_cause_category_mapping(fra_cause_codes):
    cause_category_mapping = {}
    for main_category, subcategories in fra_cause_codes.items():
        for subcategory, causes in subcategories.items():
            if isinstance(causes, dict):
                for code, _ in causes.items():
                    cause_category_mapping[code] = subcategory
            else:
                cause_category_mapping[subcategory] = main_category
    return cause_category_mapping


# Generate the mapping
cause_category_mapping = generate_cause_category_mapping(fra_cause_codes)

config = states_alphabetical

# A rough polygon for the U.S. (including Alaska and Hawaii)
US_POLYGON = Polygon([
    (-179.15, 71.39),  # Top-left (Alaska)
    (-130, 50),  # Approx west-coast mainland
    (-125, 30),  # South-west coast
    (-105, 25),  # Southern mainland
    (-80, 25),  # Florida
    (-65, 45),  # North-east coast
    (-75, 50),  # Near New England
    (-100, 60),  # Mid-west to Alaska
    (-179.15, 71.39)  # Close the loop
])
