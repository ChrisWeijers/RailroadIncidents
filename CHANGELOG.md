# Changelog

## 26 November 2024
### Added (Bilgin)
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
