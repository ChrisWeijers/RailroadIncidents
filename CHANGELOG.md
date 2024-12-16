# Changelog

## 12 December 2024
### Refactored (Bilgin)
- Splitted up [`app.py`](app.py)
  - [`app.py`](app.py) Still configures the whole dashboard by importing the necessary modules, but it readability has improved.
  - [`config.py`](GUI/config.py) contains the configuration for the sliders of the filter module
  - [`callbacks.py`](GUI/callbacks.py) contains all callbacks that handle updates for the dashboard
  - [`layout.py`](GUI/layout.py) contains the HTML layout structure of the dashboard
### Added (Bilgin)
- Added a `deselect` button when a state is selected
  - When hovering over this button, it turns into red to indicate it clearly
  - **Although the selection seems to return when zooming in or dragging the map around!!!**
- Added hover information to the arrow button.
  - When the arrow is pointing down it will say 'Switch to filters'
  - When the arrow is pointing up it will say 'Switch to barchart'

## 11 December 2024
### Added (Chris)
- Added button to sidebar to switch between the barchart and filters
### Fixes (Chris)
- Adjusted the dashboard such that it fits for different screen sizes
- Fixed the barchart such that it is readable

## 26 November 2024
### Added (Bilgin) NOT USED ANYMORE
- Added Rail_Mileposts dataset to the repository
- Implemented Python script for crash and milepost data analysis including:
  - Data loading and cleaning functions for both crash and milepost datasets
  - Spatial matching algorithm using BallTree for coordinate-based matching
  - Milepost number-based matching for records without coordinates
  - Interactive dashboard with:
    - US map showing crash locations and mileposts
    - Crash frequency analysis by year
    - Top 10 railroads by crash count
    - Top 10 states by crash count
  - Statistical analysis showing:
    - Successfully matched ~100,582 crashes (45.7% of total crashes)
    - 65,518 matches using coordinates
    - 35,064 matches using milepost numbers
    - Coverage across 752 unique railroads

## 22 November 2024
### Updated
- Wrote the [readme](https://github.com/ChrisWeijers/RailroadIncidents/edit/main/README.md) out for a detail overview of the project.
