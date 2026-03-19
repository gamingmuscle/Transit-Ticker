create database if not exists transit_ticker;
use transit_ticker;

drop table if exists stops;
CREATE TABLE stops (
    stop_id VARCHAR(64) PRIMARY KEY,
    stop_code VARCHAR(64),
    stop_name VARCHAR(255) NOT NULL,
    stop_desc VARCHAR(255),
    stop_lat DECIMAL(10,7) NOT NULL,
    stop_lon DECIMAL(10,7) NOT NULL,
    zone_id VARCHAR(64),
    stop_url VARCHAR(255),
    location_type TINYINT,
    parent_station VARCHAR(64),
    wheelchair_boarding TINYINT,
    platform_code VARCHAR(64)
);

drop table if exists routes;
CREATE TABLE routes (
    route_id VARCHAR(64) PRIMARY KEY,
    agency_id VARCHAR(64),
    route_short_name VARCHAR(64),
    route_long_name VARCHAR(255),
    route_desc VARCHAR(255),
    route_type INT NOT NULL,
    route_url VARCHAR(255),
    route_color CHAR(6),
    route_text_color CHAR(6),
    foreign key (agency_id) references agency(agency_id)
);

drop table if exists calendar;
CREATE TABLE calendar (
    service_id VARCHAR(64) PRIMARY KEY,
    monday TINYINT NOT NULL,
    tuesday TINYINT NOT NULL,
    wednesday TINYINT NOT NULL,
    thursday TINYINT NOT NULL,
    friday TINYINT NOT NULL,
    saturday TINYINT NOT NULL,
    sunday TINYINT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL
);

drop table if exists calendar_dates;
CREATE TABLE calendar_dates (
    service_id VARCHAR(64),
    date DATE NOT NULL,
    exception_type TINYINT NOT NULL,
    PRIMARY KEY (service_id, date)
);

drop table if exists trips;
CREATE TABLE trips (
    route_id VARCHAR(64) NOT NULL,
    service_id VARCHAR(64) NOT NULL,
    trip_id VARCHAR(64) PRIMARY KEY,
    trip_headsign VARCHAR(255),
    trip_short_name VARCHAR(64),
    direction_id TINYINT,
    block_id VARCHAR(64),
    shape_id VARCHAR(64),
    wheelchair_accessible TINYINT,
    bikes_allowed TINYINT,
    foreign key (route_id) references routes(route_id)
);

drop table if exists stop_times;
CREATE TABLE stop_times (
    trip_id VARCHAR(64) NOT NULL,
    arrival_time VARCHAR(8),
    departure_time VARCHAR(8),
    stop_id VARCHAR(64) NOT NULL,
    stop_sequence INT NOT NULL,
    stop_headsign VARCHAR(255),
    pickup_type TINYINT,
    drop_off_type TINYINT,
    shape_dist_traveled DECIMAL(10,3),
    timepoint TINYINT,
    PRIMARY KEY (trip_id, stop_sequence),
    INDEX idx_stop_id (stop_id),
    foreign key (trip_id) references trips(trip_id),
    foreign key (stop_id) references stops(stop_id)
);

drop table if exists shapes;
CREATE TABLE shapes (
    shape_id VARCHAR(64) NOT NULL,
    shape_pt_lat DECIMAL(10,7) NOT NULL,
    shape_pt_lon DECIMAL(10,7) NOT NULL,
    shape_pt_sequence INT NOT NULL,
    shape_dist_traveled DECIMAL(10,3),
    PRIMARY KEY (shape_id, shape_pt_sequence)
);

drop table if exists agency;
CREATE TABLE agency (
    agency_id VARCHAR(64) PRIMARY KEY,
    agency_name VARCHAR(255) NOT NULL,
    agency_url VARCHAR(255) NOT NULL,
    agency_timezone VARCHAR(64) NOT NULL,
    agency_lang VARCHAR(16),
    agency_phone VARCHAR(64),
    agency_fare_url VARCHAR(255),
    agency_email VARCHAR(255)
);

CREATE INDEX idx_stop_times_trip ON stop_times (trip_id);
CREATE INDEX idx_stop_times_stop ON stop_times (stop_id);
CREATE INDEX idx_trips_route ON trips (route_id);
CREATE INDEX idx_trips_service ON trips (service_id);
