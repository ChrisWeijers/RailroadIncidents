# Data Visualization Dashboard (Railroad Incidents)

![License](https://img.shields.io/github/license/ChrisWeijers/RailroadIncidents)
![Last Commit](https://img.shields.io/github/last-commit/ChrisWeijers/RailroadIncidents)

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Running the Dashboard](#running-the-dashboard)
- [Usage](#usage)
- [Dataset](#dataset)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Introduction
This project is a data visualization dashboard designed to provide insights into [Railroad Incidents in the US]. The dashboard uses interactive charts and tables to allow users to explore trends, patterns, and outliers in the data effectively. The goal is to make complex data more accessible and interpretable for non-technical stakeholders and users.

## Features
- Interactive visualizations (line charts, bar graphs, maps, etc.)
- Filtering and drill-down capabilities
- Customizable data views
- Downloadable reports and visualizations

## Tech Stack
- **Frontend**: [Dash]
- **Backend**: Python
- **Data Processing**: Python (pandas, numpy)
- **Visualization Libraries**: Plotly, Dash, Matplotlib
- **Deployment**: Docker (TBD)

## Getting Started

### Prerequisites
Make sure you have the following software installed:
- Python >= 3.11
- Pycharm (recommended)
- Docker (optional, for containerization)

### Installation
1. **Clone the Repository**
    ```sh
    git clone https://github.com/ChrisWeijers/RailroadIncidents.git
    cd yourrepo
    ```
2. **Create a Virtual Environment** (recommended)
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3. **Install Dependencies**
    ```sh
    pip install -r requirements.txt
    ```

### Running the Dashboard
1. **Run the Application**
    ```sh
    python app.py
    ```
2. **Access the Dashboard**  
   The dashboard will be available at `http://127.0.0.1:8050/` in your web browser.

## Usage
Once the dashboard is running, you can:
1. Use the filters on the left sidebar to adjust the data being visualized.
2. Hover over the charts for detailed tooltips.
3. Download charts as images by clicking the download icon.
4. Export filtered data as CSV for offline analysis.

## Dataset
The dataset used in this project is sourced from [U.S. Department of Transportation](https://data.transportation.gov/).
- **Name**: Railroad Equipment Accident/Incident
- **Description**: Detailed records of railroad equipment accidents and incidents in the US.
- **Link**: [Railroad Incidents](https://data.transportation.gov/Railroads/Railroad-Equipment-Accident-Incident-Source-Data-F/aqxq-n5hy/about_data)

Make sure to comply with any licensing terms of the dataset.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

---

## License
The Raidroad Incidents visualization dashboard is open-sourced software licensed under the [MIT license](https://github.com/ChrisWeijers/RailroadIncidents/blob/main/LICENSE.md).

## Contact
- **Bjorn Albers** - 
- **Bilgin Eren** - [@bilginn7](https://github.com/bilginn7)
- **Junior Jansen** - [@JuniorJansen](https://github.com/JuniorJansen)
- **Chris Weijers** - [@ChrisWeijers](https://github.com/ChrisWeijers)

Feel free to open an issue if you have any questions or suggestions regarding the project.

---

### Changelog
For a detailed list of changes, see the [Changelog](https://github.com/ChrisWeijers/RailroadIncidents/blob/main/CHANGELOG.md).

### Additional Notes:
- Limitations: 
- Future Improvements: 
