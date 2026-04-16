import mysql.connector


class DBHandler:
    """Generic, reusable MySQL database utility.
    Contains no domain-specific SQL — all query logic lives in loader classes."""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor()

    # ------------------------------------------------------------------
    # Query execution
    # ------------------------------------------------------------------

    def execute(self, sql: str, params: tuple = ()):
        """Execute a single statement. Returns self for chaining."""
        self.cursor.execute(sql, params)
        return self

    def executemany(self, sql: str, params_list: list):
        """Execute a statement against a list of parameter tuples."""
        self.cursor.executemany(sql, params_list)
        return self

    # ------------------------------------------------------------------
    # Result fetching
    # ------------------------------------------------------------------

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    @property
    def lastrowid(self) -> int:
        return self.cursor.lastrowid

    # ------------------------------------------------------------------
    # Bulk insert
    # ------------------------------------------------------------------

    def bulk_insert(self, table: str, columns: list[str],
                    rows, batch_size: int = 1000) -> int:
        """Insert an iterable of row tuples into table in batches.
        Returns total rows inserted."""
        col_names    = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

        batch = []
        count = 0

        for row in rows:
            batch.append(row)
            if len(batch) >= batch_size:
                self.cursor.executemany(sql, batch)
                count += len(batch)
                batch = []

        if batch:
            self.cursor.executemany(sql, batch)
            count += len(batch)

        return count

    # ------------------------------------------------------------------
    # Transaction control
    # ------------------------------------------------------------------

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
