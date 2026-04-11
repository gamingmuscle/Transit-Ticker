# Transit Ticker

A data pipeline for ingesting and storing NJ Transit GTFS (General Transit Feed Specification) data into a relational database.

## Overview

Transit Ticker downloads GTFS static data from NJ Transit (rail and bus), and loads it into a MySQL database for querying and analysis. The schema follows the standard GTFS specification.

## Project Structure

```
Transit-Ticker/
├── config/
│   └── GTFS.json          # Data source configuration (URLs, headers, destinations)
├── data/
│   └── NJTRANSIT/
│       ├── rail_data.zip  # Downloaded rail GTFS data
│       └── bus_data.zip   # Downloaded bus GTFS data
├── processes/
│   └── FetchGTFS.py       # Script to download GTFS zip files
└── db_setup.sql           # MySQL schema setup
```

## Requirements

- Python 3.x
- `requests` library
- MySQL

Install Python dependencies:

```bash
pip install requests
```

## Setup

### 1. Database

Run the setup script against your MySQL instance:

```bash
mysql -u <user> -p < db_setup.sql
```

This creates the `transit_ticker` database with the following tables:

| Table            | Description                              |
|------------------|------------------------------------------|
| `agency`         | Transit agency info                      |
| `stops`          | Stop locations and metadata              |
| `routes`         | Route definitions                        |
| `trips`          | Individual trip records                  |
| `stop_times`     | Arrival/departure times per stop per trip|
| `calendar`       | Weekly service schedules                 |
| `calendar_dates` | Service exceptions (holidays, etc.)      |
| `shapes`         | Geographic route shapes                  |

### 2. Download GTFS Data

Run the fetch script from the `processes/` directory:

```bash
cd processes
python FetchGTFS.py
```

This reads `config/GTFS.json` and downloads the configured GTFS zip files to `data/NJTRANSIT/`.

## Configuration

`config/GTFS.json` defines the data sources. Each entry in the `ingress` array specifies:

| Field           | Description                              |
|-----------------|------------------------------------------|
| `url`           | Base URL of the data source              |
| `file`          | File name to append to the URL           |
| `destDirectory` | Local directory to save the file         |
| `destFile`      | Local file name to save as               |
| `request`       | HTTP method, params, payload, and headers|

### Example entry

```json
{
    "url": "https://www.njtransit.com/",
    "file": "rail_data.zip",
    "destDirectory": "data/NJTRANSIT/",
    "destFile": "rail_data.zip",
    "request": {
        "method": "GET",
        "params": {},
        "payload": null,
        "headers": {
            "User-Agent": "Mozilla/5.0 ..."
        }
    }
}
```

## Data Sources

- [NJ Transit GTFS](https://www.njtransit.com/) — rail and bus static schedule data
