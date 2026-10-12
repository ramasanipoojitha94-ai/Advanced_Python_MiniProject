from yatrago import db


def migrate_reusable_bus_seats():
    """Remove the legacy passenger-seat uniqueness while keeping booking history intact."""
    if db.engine.dialect.name != "sqlite":
        return
    connection = db.engine.raw_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        indexes = cursor.execute("PRAGMA index_list('passenger')").fetchall()
        legacy_unique = False
        for index in indexes:
            if index[2]:
                columns = cursor.execute(f"PRAGMA index_info('{index[1]}')").fetchall()
                if [column[2] for column in columns] == ["seat_id"]:
                    legacy_unique = True
                    break
        if not legacy_unique:
            return

        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute(
            """
            CREATE TABLE passenger_reusable (
                id INTEGER NOT NULL PRIMARY KEY,
                booking_id INTEGER NOT NULL,
                seat_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                age INTEGER NOT NULL,
                gender VARCHAR(20) NOT NULL,
                CONSTRAINT ck_passenger_age CHECK (age BETWEEN 1 AND 120),
                FOREIGN KEY(booking_id) REFERENCES booking (id),
                FOREIGN KEY(seat_id) REFERENCES seat (id)
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO passenger_reusable (id, booking_id, seat_id, name, age, gender)
            SELECT id, booking_id, seat_id, name, age, gender FROM passenger
            """
        )
        cursor.execute("DROP TABLE passenger")
        cursor.execute("ALTER TABLE passenger_reusable RENAME TO passenger")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_passenger_booking_id ON passenger (booking_id)"
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        try:
            connection.cursor().execute("PRAGMA foreign_keys=ON")
        finally:
            connection.close()


def migrate_add_user_avatar():
    """Add avatar column to user table if missing (SQLite friendly)."""
    if db.engine.dialect.name != "sqlite":
        return
    conn = db.engine.raw_connection()
    try:
        cur = conn.cursor()
        cols = [row[1] for row in cur.execute("PRAGMA table_info('user')").fetchall()]
        if 'avatar' in cols:
            return
        cur.execute("BEGIN IMMEDIATE")
        cur.execute("ALTER TABLE user ADD COLUMN avatar VARCHAR(300)")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
