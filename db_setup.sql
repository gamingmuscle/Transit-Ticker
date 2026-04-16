CREATE DATABASE IF NOT EXISTS transit_ticker;
USE transit_ticker;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- RT TABLES (drop first, reverse dependency order)
-- ============================================================
DROP TABLE IF EXISTS alert_translations;
DROP TABLE IF EXISTS alert_informed_entities;
DROP TABLE IF EXISTS alert_active_periods;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS stop_time_updates;
DROP TABLE IF EXISTS trip_updates;
DROP TABLE IF EXISTS vehicle_carriage_details;
DROP TABLE IF EXISTS vehicle_positions;
DROP TABLE IF EXISTS feed_fetches;
DROP TABLE IF EXISTS rt_authorities;

-- ============================================================
-- STATIC GTFS TABLES (drop first, reverse dependency order)
-- ============================================================
DROP TABLE IF EXISTS gtfs_fetches;
DROP TABLE IF EXISTS stop_times;
DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS stops;
DROP TABLE IF EXISTS calendar_dates;
DROP TABLE IF EXISTS calendar;
DROP TABLE IF EXISTS shapes;
DROP TABLE IF EXISTS agency;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- STATIC GTFS TABLES
-- ============================================================

CREATE TABLE agency (
    agency_id       VARCHAR(64)  PRIMARY KEY,
    agency_name     VARCHAR(255) NOT NULL,
    agency_url      VARCHAR(255) NOT NULL,
    agency_timezone VARCHAR(64)  NOT NULL,
    agency_lang     VARCHAR(16),
    agency_phone    VARCHAR(64),
    agency_fare_url VARCHAR(255),
    agency_email    VARCHAR(255)
);

CREATE TABLE stops (
    agency_id   VARCHAR(64),
    stop_id     VARCHAR(64)   PRIMARY KEY,
    stop_code   VARCHAR(64),
    stop_name   VARCHAR(255)  NOT NULL,
    stop_desc   VARCHAR(255),
    stop_lat    DECIMAL(10,7) NOT NULL,
    stop_lon    DECIMAL(10,7) NOT NULL,
    zone_id     VARCHAR(64),
    stop_url    VARCHAR(255),
    location_type       TINYINT,
    parent_station      VARCHAR(64),
    wheelchair_boarding TINYINT,
    platform_code       VARCHAR(64),
    FOREIGN KEY (agency_id) REFERENCES agency(agency_id)
);

CREATE TABLE routes (
    route_id         VARCHAR(64),
    agency_id        VARCHAR(64),
    route_short_name VARCHAR(64),
    route_long_name  VARCHAR(255),
    route_desc       VARCHAR(255),
    route_type       INT NOT NULL,
    route_url        VARCHAR(255),
    route_color      CHAR(6),
    route_text_color CHAR(6),
    PRIMARY KEY (route_id, agency_id),
    FOREIGN KEY (agency_id) REFERENCES agency(agency_id)
);

CREATE TABLE calendar (
    service_id VARCHAR(64) PRIMARY KEY,
    monday     TINYINT NOT NULL,
    tuesday    TINYINT NOT NULL,
    wednesday  TINYINT NOT NULL,
    thursday   TINYINT NOT NULL,
    friday     TINYINT NOT NULL,
    saturday   TINYINT NOT NULL,
    sunday     TINYINT NOT NULL,
    start_date DATE NOT NULL,
    end_date   DATE NOT NULL
);

CREATE TABLE calendar_dates (
    service_id     VARCHAR(64),
    date           DATE    NOT NULL,
    exception_type TINYINT NOT NULL,
    PRIMARY KEY (service_id, date)
);

CREATE TABLE trips (
    route_id              VARCHAR(64) NOT NULL,
    service_id            VARCHAR(64) NOT NULL,
    trip_id               VARCHAR(64) PRIMARY KEY,
    trip_headsign         VARCHAR(255),
    trip_short_name       VARCHAR(64),
    direction_id          TINYINT,
    block_id              VARCHAR(64),
    shape_id              VARCHAR(64),
    wheelchair_accessible TINYINT,
    bikes_allowed         TINYINT,
    FOREIGN KEY (route_id) REFERENCES routes(route_id)
);

CREATE TABLE stop_times (
    trip_id             VARCHAR(64) NOT NULL,
    arrival_time        VARCHAR(8),
    departure_time      VARCHAR(8),
    stop_id             VARCHAR(64) NOT NULL,
    stop_sequence       INT         NOT NULL,
    stop_headsign       VARCHAR(255),
    pickup_type         TINYINT,
    drop_off_type       TINYINT,
    shape_dist_traveled DECIMAL(10,3),
    timepoint           TINYINT,
    PRIMARY KEY (trip_id, stop_sequence),
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
);

-- agency_id added (non-standard) so shapes can be cleared per-agency
-- when rail and bus feeds are loaded independently
CREATE TABLE shapes (
    agency_id           VARCHAR(64)   NOT NULL,
    shape_id            VARCHAR(64)   NOT NULL,
    shape_pt_lat        DECIMAL(10,7) NOT NULL,
    shape_pt_lon        DECIMAL(10,7) NOT NULL,
    shape_pt_sequence   INT           NOT NULL,
    shape_dist_traveled DECIMAL(10,3),
    PRIMARY KEY (agency_id, shape_id, shape_pt_sequence),
    FOREIGN KEY (agency_id) REFERENCES agency(agency_id)
);

-- Audit log: one row per GTFS zip downloaded and loaded
CREATE TABLE gtfs_fetches (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    authority  VARCHAR(64)  NOT NULL,   -- matches "authority" in GTFS.json
    file       VARCHAR(255) NOT NULL,   -- e.g. "rail_data.zip"
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    row_counts JSON,                    -- {"agency.txt": 1, "stops.txt": 500, ...}
    status     TINYINT NOT NULL DEFAULT 1  COMMENT '1=success, 0=failure'
);

-- ============================================================
-- RT AUTHORITY & AUDIT LOG
-- ============================================================

CREATE TABLE rt_authorities (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    authority  VARCHAR(64)  NOT NULL UNIQUE,
    url        VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feed_fetches (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    authority_id  INT UNSIGNED NOT NULL,
    endpoint      VARCHAR(128) NOT NULL,
    entity_type   VARCHAR(64)  NOT NULL,
    fetched_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feed_timestamp  BIGINT,
    feed_version    VARCHAR(16),
    entity_count    INT UNSIGNED DEFAULT 0,
    status        TINYINT NOT NULL DEFAULT 1  COMMENT '1=success, 0=failure',
    FOREIGN KEY (authority_id) REFERENCES rt_authorities(id)
);

-- ============================================================
-- VEHICLE POSITIONS
-- ============================================================

CREATE TABLE vehicle_positions (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    authority_id  INT UNSIGNED NOT NULL,
    entity_id     VARCHAR(64)  NOT NULL,
    last_fetch_id INT UNSIGNED,

    vehicle_id    VARCHAR(64),
    vehicle_label VARCHAR(255),

    trip_id               VARCHAR(64),
    route_id              VARCHAR(64),
    direction_id          TINYINT,
    start_time            VARCHAR(16),
    start_date            CHAR(8),
    schedule_relationship TINYINT  COMMENT '0=SCHEDULED,1=ADDED,2=UNSCHEDULED,3=CANCELED',

    latitude   DECIMAL(10,7),
    longitude  DECIMAL(10,7),
    bearing    FLOAT,
    speed      FLOAT,
    odometer   DOUBLE,

    current_stop_sequence INT UNSIGNED,
    stop_id               VARCHAR(64),
    current_status        TINYINT  COMMENT '0=INCOMING_AT,1=STOPPED_AT,2=IN_TRANSIT_TO',

    congestion_level     TINYINT   COMMENT '0=UNKNOWN,1=RUNNING_SMOOTHLY,2=STOP_AND_GO,3=CONGESTION,4=SEVERE_CONGESTION',
    occupancy_status     TINYINT   COMMENT '0=EMPTY,1=MANY_SEATS_AVAILABLE,2=FEW_SEATS_AVAILABLE,3=STANDING_ROOM_ONLY,4=CRUSHED_STANDING_ROOM_ONLY,5=FULL,6=NOT_ACCEPTING_PASSENGERS,7=NO_DATA_AVAILABLE,8=NOT_BOARDABLE',
    occupancy_percentage TINYINT UNSIGNED,

    timestamp  BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_vp_authority_entity (authority_id, entity_id),
    FOREIGN KEY (authority_id)  REFERENCES rt_authorities(id),
    FOREIGN KEY (last_fetch_id) REFERENCES feed_fetches(id) ON DELETE SET NULL
);

CREATE TABLE vehicle_carriage_details (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    vehicle_position_id INT UNSIGNED NOT NULL,
    authority_id        INT UNSIGNED NOT NULL,
    carriage_sequence   TINYINT UNSIGNED,
    carriage_id         VARCHAR(64),
    label               VARCHAR(255),
    occupancy_status    TINYINT,
    occupancy_percentage TINYINT UNSIGNED,
    FOREIGN KEY (vehicle_position_id) REFERENCES vehicle_positions(id) ON DELETE CASCADE,
    FOREIGN KEY (authority_id)        REFERENCES rt_authorities(id)
);

-- ============================================================
-- TRIP UPDATES
-- ============================================================

CREATE TABLE trip_updates (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    authority_id  INT UNSIGNED NOT NULL,
    entity_id     VARCHAR(64)  NOT NULL,
    last_fetch_id INT UNSIGNED,

    trip_id               VARCHAR(64),
    route_id              VARCHAR(64),
    direction_id          TINYINT,
    start_time            VARCHAR(16),
    start_date            CHAR(8),
    schedule_relationship TINYINT  COMMENT '0=SCHEDULED,1=ADDED,2=UNSCHEDULED,3=CANCELED,5=REPLACEMENT,6=DUPLICATED,7=DELETED,8=NEW',

    vehicle_id    VARCHAR(64),
    vehicle_label VARCHAR(255),

    timestamp  BIGINT,
    delay      INT,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_tu_authority_entity (authority_id, entity_id),
    FOREIGN KEY (authority_id)  REFERENCES rt_authorities(id),
    FOREIGN KEY (last_fetch_id) REFERENCES feed_fetches(id) ON DELETE SET NULL
);

CREATE TABLE stop_time_updates (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    trip_update_id INT UNSIGNED NOT NULL,
    authority_id   INT UNSIGNED NOT NULL,

    stop_sequence INT UNSIGNED,
    stop_id       VARCHAR(64),

    arrival_delay          INT,
    arrival_time           BIGINT,
    arrival_uncertainty    INT,
    arrival_scheduled_time BIGINT,

    departure_delay          INT,
    departure_time           BIGINT,
    departure_uncertainty    INT,
    departure_scheduled_time BIGINT,

    schedule_relationship TINYINT  COMMENT '0=SCHEDULED,1=SKIPPED,2=NO_DATA,3=UNSCHEDULED',
    stop_headsign         VARCHAR(255),
    assigned_stop_id      VARCHAR(64),

    FOREIGN KEY (trip_update_id) REFERENCES trip_updates(id) ON DELETE CASCADE,
    FOREIGN KEY (authority_id)   REFERENCES rt_authorities(id)
);

-- ============================================================
-- ALERTS
-- ============================================================

CREATE TABLE alerts (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    authority_id  INT UNSIGNED NOT NULL,
    entity_id     VARCHAR(64)  NOT NULL,
    last_fetch_id INT UNSIGNED,

    cause          TINYINT  COMMENT '1=UNKNOWN_CAUSE,2=OTHER_CAUSE,3=TECHNICAL_PROBLEM,4=STRIKE,5=DEMONSTRATION,6=ACCIDENT,7=HOLIDAY,8=WEATHER,9=MAINTENANCE,10=CONSTRUCTION,11=POLICE_ACTIVITY,12=MEDICAL_EMERGENCY',
    effect         TINYINT  COMMENT '1=NO_SERVICE,2=REDUCED_SERVICE,3=SIGNIFICANT_DELAYS,4=DETOUR,5=ADDITIONAL_SERVICE,6=MODIFIED_SERVICE,7=OTHER_EFFECT,8=UNKNOWN_EFFECT,9=STOP_MOVED,10=NO_EFFECT,11=ACCESSIBILITY_ISSUE',
    severity_level TINYINT  COMMENT '1=UNKNOWN_SEVERITY,2=INFO,3=WARNING,4=SEVERE',

    url              VARCHAR(512),
    header_text      TEXT,
    description_text TEXT,
    cause_detail     TEXT,
    effect_detail    TEXT,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_alert_authority_entity (authority_id, entity_id),
    FOREIGN KEY (authority_id)  REFERENCES rt_authorities(id),
    FOREIGN KEY (last_fetch_id) REFERENCES feed_fetches(id) ON DELETE SET NULL
);

CREATE TABLE alert_active_periods (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    alert_id     INT UNSIGNED NOT NULL,
    authority_id INT UNSIGNED NOT NULL,
    start_time   BIGINT,
    end_time     BIGINT,
    FOREIGN KEY (alert_id)     REFERENCES alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (authority_id) REFERENCES rt_authorities(id)
);

CREATE TABLE alert_informed_entities (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    alert_id        INT UNSIGNED NOT NULL,
    authority_id    INT UNSIGNED NOT NULL,
    agency_selector VARCHAR(64),
    route_id        VARCHAR(64),
    route_type      INT,
    direction_id    TINYINT,
    trip_id         VARCHAR(64),
    stop_id         VARCHAR(64),
    FOREIGN KEY (alert_id)     REFERENCES alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (authority_id) REFERENCES rt_authorities(id)
);

CREATE TABLE alert_translations (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    alert_id     INT UNSIGNED NOT NULL,
    authority_id INT UNSIGNED NOT NULL,
    field_name   VARCHAR(64)  NOT NULL  COMMENT 'url,header_text,description_text,tts_header_text,tts_description_text,cause_detail,effect_detail,image_alternative_text',
    language     VARCHAR(16),
    text_value   TEXT,
    image_url    VARCHAR(512),
    image_media_type VARCHAR(64),
    FOREIGN KEY (alert_id)     REFERENCES alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (authority_id) REFERENCES rt_authorities(id)
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Static GTFS
CREATE INDEX idx_stop_times_trip  ON stop_times (trip_id);
CREATE INDEX idx_stop_times_stop  ON stop_times (stop_id);
CREATE INDEX idx_trips_route      ON trips (route_id);
CREATE INDEX idx_trips_service    ON trips (service_id);
CREATE INDEX idx_shapes_agency    ON shapes (agency_id);
CREATE INDEX idx_gtfs_fetches_auth ON gtfs_fetches (authority);

-- RT: filter by authority
CREATE INDEX idx_vp_authority    ON vehicle_positions (authority_id);
CREATE INDEX idx_vcd_authority   ON vehicle_carriage_details (authority_id);
CREATE INDEX idx_tu_authority    ON trip_updates (authority_id);
CREATE INDEX idx_stu_authority   ON stop_time_updates (authority_id);
CREATE INDEX idx_alert_authority ON alerts (authority_id);
CREATE INDEX idx_aap_authority   ON alert_active_periods (authority_id);
CREATE INDEX idx_aie_authority   ON alert_informed_entities (authority_id);
CREATE INDEX idx_at_authority    ON alert_translations (authority_id);
CREATE INDEX idx_ff_authority    ON feed_fetches (authority_id);

-- RT: common query patterns
CREATE INDEX idx_vp_trip   ON vehicle_positions (trip_id);
CREATE INDEX idx_vp_route  ON vehicle_positions (route_id);
CREATE INDEX idx_tu_trip   ON trip_updates (trip_id);
CREATE INDEX idx_tu_route  ON trip_updates (route_id);
CREATE INDEX idx_stu_stop  ON stop_time_updates (stop_id);
CREATE INDEX idx_aie_route ON alert_informed_entities (route_id);
CREATE INDEX idx_aie_stop  ON alert_informed_entities (stop_id);
CREATE INDEX idx_aie_trip  ON alert_informed_entities (trip_id);
