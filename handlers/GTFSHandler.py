import csv
import io
import zipfile


class GTFSHandler:

    # Maps each GTFS filename to its DB table and insertion column order.
    # inject_agency_id: True means agency_id is not in the CSV and must be
    # prepended from the feed's own agency record.
    FILE_TABLE_MAP = {
        'agency.txt': {
            'table': 'agency',
            'columns': [
                'agency_id', 'agency_name', 'agency_url', 'agency_timezone',
                'agency_lang', 'agency_phone', 'agency_fare_url', 'agency_email',
            ],
            'inject_agency_id': False,
        },
        'stops.txt': {
            'table': 'stops',
            'columns': [
                'agency_id',
                'stop_id', 'stop_code', 'stop_name', 'stop_desc',
                'stop_lat', 'stop_lon', 'zone_id', 'stop_url',
                'location_type', 'parent_station', 'wheelchair_boarding', 'platform_code',
            ],
            'inject_agency_id': True,
        },
        'routes.txt': {
            'table': 'routes',
            'columns': [
                'route_id', 'agency_id', 'route_short_name', 'route_long_name',
                'route_desc', 'route_type', 'route_url', 'route_color', 'route_text_color',
            ],
            'inject_agency_id': False,
        },
        'calendar.txt': {
            'table': 'calendar',
            'columns': [
                'service_id', 'monday', 'tuesday', 'wednesday', 'thursday',
                'friday', 'saturday', 'sunday', 'start_date', 'end_date',
            ],
            'inject_agency_id': False,
        },
        'calendar_dates.txt': {
            'table': 'calendar_dates',
            'columns': ['service_id', 'date', 'exception_type'],
            'inject_agency_id': False,
        },
        'trips.txt': {
            'table': 'trips',
            'columns': [
                'route_id', 'service_id', 'trip_id', 'trip_headsign', 'trip_short_name',
                'direction_id', 'block_id', 'shape_id', 'wheelchair_accessible', 'bikes_allowed',
            ],
            'inject_agency_id': False,
        },
        'stop_times.txt': {
            'table': 'stop_times',
            'columns': [
                'trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence',
                'stop_headsign', 'pickup_type', 'drop_off_type', 'shape_dist_traveled', 'timepoint',
            ],
            'inject_agency_id': False,
        },
        'shapes.txt': {
            'table': 'shapes',
            'columns': [
                'agency_id',
                'shape_id', 'shape_pt_lat', 'shape_pt_lon',
                'shape_pt_sequence', 'shape_dist_traveled',
            ],
            'inject_agency_id': True,
        },
    }

    # FK-safe load order — each file only references tables already loaded
    LOAD_ORDER = [
        'agency.txt',
        'stops.txt',
        'routes.txt',
        'calendar.txt',
        'calendar_dates.txt',
        'trips.txt',
        'stop_times.txt',
        'shapes.txt',
    ]

    def __init__(self, zip_path: str):
        self.zip_path = zip_path
        self._zip = zipfile.ZipFile(zip_path, 'r')
        # Normalise to bare filenames (some feeds nest inside a subdirectory)
        self._files = {
            name.split('/')[-1]: name
            for name in self._zip.namelist()
            if name.endswith('.txt')
        }

    def get_files(self) -> list[str]:
        """Return bare filenames present in the zip (e.g. ['agency.txt', 'stops.txt', ...])."""
        return list(self._files.keys())

    def read_file(self, filename: str):
        """Stream rows from a GTFS CSV file as dicts. Handles UTF-8 BOM."""
        if filename not in self._files:
            return
        with self._zip.open(self._files[filename]) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
            for row in reader:
                yield row

    def get_primary_agency_id(self) -> str | None:
        """Read agency.txt and return the first agency_id found."""
        for row in self.read_file('agency.txt'):
            return row.get('agency_id') or None
        return None

    def close(self):
        self._zip.close()
