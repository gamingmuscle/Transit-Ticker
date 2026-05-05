from handlers.DBHandler import DBHandler


class RTHandler:
    """Domain-specific RT database operations built on top of the generic DBHandler."""

    def __init__(self, db: DBHandler):
        self.db = db

    # ------------------------------------------------------------------
    # Authority
    # ------------------------------------------------------------------

    def get_or_create_authority(self, authority: str, url: str) -> int:
        self.db.execute(
            "SELECT id FROM rt_authorities WHERE authority = %s", (authority,)
        )
        row = self.db.fetchone()
        if row:
            return row[0]
        self.db.execute(
            "INSERT INTO rt_authorities (authority, url) VALUES (%s, %s)",
            (authority, url),
        )
        self.db.commit()
        return self.db.lastrowid

    # ------------------------------------------------------------------
    # Fetch log
    # ------------------------------------------------------------------

    def log_fetch(self, authority_id: int, endpoint: str, entity_type: str, parsed) -> int:
        header = parsed.header
        self.db.execute(
            """INSERT INTO feed_fetches
               (authority_id, endpoint, entity_type, feed_timestamp, feed_version, entity_count)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                authority_id,
                endpoint,
                entity_type,
                header.timestamp or None,
                header.gtfs_realtime_version or None,
                len(parsed.entity),
            ),
        )
        self.db.commit()
        return self.db.lastrowid

    # ------------------------------------------------------------------
    # Entity dispatch
    # ------------------------------------------------------------------

    def insert_entities(self, authority_id: int, fetch_id: int, parsed):
        for entity in parsed.entity:
            if entity.HasField("vehicle"):
                self._upsert_vehicle_position(authority_id, fetch_id, entity)
            elif entity.HasField("trip_update"):
                self._upsert_trip_update(authority_id, fetch_id, entity)
            elif entity.HasField("alert"):
                self._upsert_alert(authority_id, fetch_id, entity)
        self.db.commit()

    # ------------------------------------------------------------------
    # Vehicle positions
    # ------------------------------------------------------------------

    def _upsert_vehicle_position(self, authority_id: int, fetch_id: int, entity):
        vp      = entity.vehicle
        trip    = vp.trip
        pos     = vp.position
        vehicle = vp.vehicle

        self.db.execute(
            """INSERT INTO vehicle_positions
               (authority_id, entity_id, last_fetch_id,
                vehicle_id, vehicle_label,
                trip_id, route_id, direction_id, start_time, start_date, schedule_relationship,
                latitude, longitude, bearing, speed, odometer,
                current_stop_sequence, stop_id, current_status,
                congestion_level, occupancy_status, occupancy_percentage, timestamp)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE
                 id                    = LAST_INSERT_ID(id),
                 last_fetch_id         = VALUES(last_fetch_id),
                 vehicle_id            = VALUES(vehicle_id),
                 vehicle_label         = VALUES(vehicle_label),
                 trip_id               = VALUES(trip_id),
                 route_id              = VALUES(route_id),
                 direction_id          = VALUES(direction_id),
                 start_time            = VALUES(start_time),
                 start_date            = VALUES(start_date),
                 schedule_relationship = VALUES(schedule_relationship),
                 latitude              = VALUES(latitude),
                 longitude             = VALUES(longitude),
                 bearing               = VALUES(bearing),
                 speed                 = VALUES(speed),
                 odometer              = VALUES(odometer),
                 current_stop_sequence = VALUES(current_stop_sequence),
                 stop_id               = VALUES(stop_id),
                 current_status        = VALUES(current_status),
                 congestion_level      = VALUES(congestion_level),
                 occupancy_status      = VALUES(occupancy_status),
                 occupancy_percentage  = VALUES(occupancy_percentage),
                 timestamp             = VALUES(timestamp)""",
            (
                authority_id, entity.id, fetch_id,
                vehicle.id or None, vehicle.label or None,
                trip.trip_id or None, trip.route_id or None,
                trip.direction_id, trip.start_time or None, trip.start_date or None,
                trip.schedule_relationship,
                pos.latitude or None, pos.longitude or None,
                pos.bearing or None, pos.speed or None, pos.odometer or None,
                vp.current_stop_sequence or None, vp.stop_id or None,
                vp.current_status,
                vp.congestion_level, vp.occupancy_status,
                vp.occupancy_percentage or None,
                vp.timestamp or None,
            ),
        )

        vp_id = self.db.lastrowid

        if vp.multi_carriage_details:
            self.db.execute(
                "DELETE FROM vehicle_carriage_details WHERE vehicle_position_id = %s", (vp_id,)
            )
            self.db.executemany(
                """INSERT INTO vehicle_carriage_details
                   (vehicle_position_id, authority_id, carriage_sequence,
                    carriage_id, label, occupancy_status, occupancy_percentage)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                [
                    (
                        vp_id, authority_id, i,
                        c.id or None, c.label or None,
                        c.occupancy_status, c.occupancy_percentage or None,
                    )
                    for i, c in enumerate(vp.multi_carriage_details)
                ],
            )

    # ------------------------------------------------------------------
    # Trip updates
    # ------------------------------------------------------------------

    def _upsert_trip_update(self, authority_id: int, fetch_id: int, entity):
        tu      = entity.trip_update
        trip    = tu.trip
        vehicle = tu.vehicle

        self.db.execute(
            """INSERT INTO trip_updates
               (authority_id, entity_id, last_fetch_id,
                trip_id, route_id, direction_id, start_time, start_date, schedule_relationship,
                vehicle_id, vehicle_label, timestamp, delay)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE
                 id                    = LAST_INSERT_ID(id),
                 last_fetch_id         = VALUES(last_fetch_id),
                 trip_id               = VALUES(trip_id),
                 route_id              = VALUES(route_id),
                 direction_id          = VALUES(direction_id),
                 start_time            = VALUES(start_time),
                 start_date            = VALUES(start_date),
                 schedule_relationship = VALUES(schedule_relationship),
                 vehicle_id            = VALUES(vehicle_id),
                 vehicle_label         = VALUES(vehicle_label),
                 timestamp             = VALUES(timestamp),
                 delay                 = VALUES(delay)""",
            (
                authority_id, entity.id, fetch_id,
                trip.trip_id or None, trip.route_id or None,
                trip.direction_id, trip.start_time or None, trip.start_date or None,
                trip.schedule_relationship,
                vehicle.id or None, vehicle.label or None,
                tu.timestamp or None, tu.delay or None,
            ),
        )

        tu_id = self.db.lastrowid

        if tu.stop_time_update:
            self.db.execute(
                "DELETE FROM stop_time_updates WHERE trip_update_id = %s", (tu_id,)
            )
            self.db.executemany(
                """INSERT INTO stop_time_updates
                   (trip_update_id, authority_id,
                    stop_sequence, stop_id,
                    arrival_delay, arrival_time, arrival_uncertainty, arrival_scheduled_time,
                    departure_delay, departure_time, departure_uncertainty, departure_scheduled_time,
                    schedule_relationship, stop_headsign, assigned_stop_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                [
                    (
                        tu_id, authority_id,
                        stu.stop_sequence or None, stu.stop_id or None,
                        stu.arrival.delay   if stu.HasField("arrival")   else None,
                        stu.arrival.time    if stu.HasField("arrival")   else None,
                        stu.arrival.uncertainty if stu.HasField("arrival") else None,
                        None,  # arrival_scheduled_time — not in standard GTFS-RT proto
                        stu.departure.delay if stu.HasField("departure") else None,
                        stu.departure.time  if stu.HasField("departure") else None,
                        stu.departure.uncertainty if stu.HasField("departure") else None,
                        None,  # departure_scheduled_time — not in standard GTFS-RT proto
                        stu.schedule_relationship,
                        getattr(stu, "stop_headsign", None) or None,
                        getattr(stu, "assigned_stop_id", None) or None,
                    )
                    for stu in tu.stop_time_update
                ],
            )

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    def _upsert_alert(self, authority_id: int, fetch_id: int, entity):
        alert = entity.alert

        self.db.execute(
            """INSERT INTO alerts
               (authority_id, entity_id, last_fetch_id,
                cause, effect, severity_level,
                url, header_text, description_text, cause_detail, effect_detail)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE
                 id               = LAST_INSERT_ID(id),
                 last_fetch_id    = VALUES(last_fetch_id),
                 cause            = VALUES(cause),
                 effect           = VALUES(effect),
                 severity_level   = VALUES(severity_level),
                 url              = VALUES(url),
                 header_text      = VALUES(header_text),
                 description_text = VALUES(description_text),
                 cause_detail     = VALUES(cause_detail),
                 effect_detail    = VALUES(effect_detail)""",
            (
                authority_id, entity.id, fetch_id,
                alert.cause or None,
                alert.effect or None,
                getattr(alert, "severity_level", None) or None,
                _first_translation(alert.url),
                _first_translation(alert.header_text),
                _first_translation(alert.description_text),
                _first_translation(getattr(alert, "cause_detail", None)),
                _first_translation(getattr(alert, "effect_detail", None)),
            ),
        )

        alert_id = self.db.lastrowid

        self.db.execute("DELETE FROM alert_active_periods   WHERE alert_id = %s", (alert_id,))
        self.db.execute("DELETE FROM alert_informed_entities WHERE alert_id = %s", (alert_id,))
        self.db.execute("DELETE FROM alert_translations      WHERE alert_id = %s", (alert_id,))

        if alert.active_period:
            self.db.executemany(
                """INSERT INTO alert_active_periods (alert_id, authority_id, start_time, end_time)
                   VALUES (%s,%s,%s,%s)""",
                [
                    (alert_id, authority_id, ap.start or None, ap.end or None)
                    for ap in alert.active_period
                ],
            )

        if alert.informed_entity:
            self.db.executemany(
                """INSERT INTO alert_informed_entities
                   (alert_id, authority_id, agency_selector, route_id, route_type,
                    direction_id, trip_id, stop_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                [
                    (
                        alert_id, authority_id,
                        ie.agency_id or None,
                        ie.route_id or None,
                        ie.route_type or None,
                        getattr(ie, "direction_id", None) or None,
                        ie.trip.trip_id or None if ie.HasField("trip") else None,
                        ie.stop_id or None,
                    )
                    for ie in alert.informed_entity
                ],
            )

        for field_name, trans_msg in (
            ("url",              alert.url),
            ("header_text",      alert.header_text),
            ("description_text", alert.description_text),
        ):
            if trans_msg and trans_msg.translation:
                self.db.executemany(
                    """INSERT INTO alert_translations
                       (alert_id, authority_id, field_name, language, text_value, image_url, image_media_type)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    [
                        (alert_id, authority_id, field_name,
                         t.language or None, t.text or None, None, None)
                        for t in trans_msg.translation
                    ],
                )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _first_translation(trans_msg) -> str | None:
    """Return the first translation text from a TranslatedString, or None."""
    if not trans_msg or not trans_msg.translation:
        return None
    return trans_msg.translation[0].text or None
