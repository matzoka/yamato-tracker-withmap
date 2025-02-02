import sqlite3
import os

def get_messages(language='Japanese'):
    """Get messages in specified language"""
    return {
        'success': "Database has been successfully reset." if language == 'English' else "データベースを正常に初期化しました。",
        'error': "Error occurred while resetting database: {}" if language == 'English' else "データベース初期化中にエラーが発生しました: {}"
    }

def reset_database(language='Japanese'):
    """Reset database by dropping and recreating the table"""
    db_path = os.path.join(os.path.dirname(__file__), 'tracking.db')
    try:
        with sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            c = conn.cursor()
            # Set timezone
            conn.execute("PRAGMA timezone = '+9:00'")

            # Drop existing table and trigger
            c.execute('DROP TABLE IF EXISTS tracking_data')
            c.execute('DROP TRIGGER IF EXISTS set_created_at')

            # Create table
            c.execute('''CREATE TABLE tracking_data
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       tracking_number TEXT NOT NULL,
                       status TEXT,
                       place_name TEXT,
                       place_code TEXT,
                       track_date TEXT,
                       track_time TEXT,
                       place_postcode TEXT,
                       place_address TEXT,
                       place_lat REAL,
                       place_lng REAL,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       UNIQUE(tracking_number, track_date, track_time))''')

            # Create trigger
            conn.execute('''CREATE TRIGGER IF NOT EXISTS set_created_at
                          AFTER INSERT ON tracking_data
                          BEGIN
                              UPDATE tracking_data SET created_at = datetime('now', '+9 hours')
                              WHERE id = NEW.id;
                          END''')

            conn.commit()
            msgs = get_messages(language)
            return True, msgs['success']
    except Exception as e:
        return False, get_messages(language)['error'].format(str(e))

def init_db():
    """Initialize database connection and create tables"""
    db_path = os.path.join(os.path.dirname(__file__), 'tracking.db')
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    init_db_schema(conn)
    return conn

def init_db_schema(conn):
    """Initialize database schema"""
    c = conn.cursor()

    # Set timezone
    conn.execute("PRAGMA timezone = '+9:00'")

    # Create table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS tracking_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tracking_number TEXT NOT NULL,
                  status TEXT,
                  place_name TEXT,
                  place_code TEXT,
                  track_date TEXT,
                  track_time TEXT,
                  place_postcode TEXT,
                  place_address TEXT,
                  place_lat REAL,
                  place_lng REAL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  UNIQUE(tracking_number, track_date, track_time))''')

    # Create trigger if not exists
    c.execute('DROP TRIGGER IF EXISTS set_created_at')
    c.execute('''CREATE TRIGGER IF NOT EXISTS set_created_at
                 AFTER INSERT ON tracking_data
                 BEGIN
                     UPDATE tracking_data SET created_at = datetime('now', '+9 hours')
                     WHERE id = NEW.id;
                 END''')
    conn.commit()

def clear_all_data():
    """Delete all data from tracking_data table"""
    db_path = os.path.join(os.path.dirname(__file__), 'tracking.db')
    print(f"Deleting data from database at: {db_path}")  # Debug message
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM tracking_data')
        conn.commit()
        print("Data deletion completed successfully")  # Debug message

def get_tracking_data(tracking_number=None):
    """Get tracking data from database"""
    db_path = os.path.join(os.path.dirname(__file__), 'tracking.db')
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        if tracking_number:
            c.execute('''SELECT * FROM tracking_data
                        WHERE tracking_number = ?
                        ORDER BY created_at DESC''',
                     (tracking_number,))
        else:
            c.execute('''SELECT * FROM tracking_data
                        ORDER BY id DESC''')
        return c.fetchall()

def save_tracking_data(conn, tracking_data):
    """Save tracking data to database"""
    c = conn.cursor()
    for data in tracking_data[1:]:
        # Check if data already exists
        c.execute('''SELECT id FROM tracking_data
                    WHERE tracking_number = ?
                    AND track_date = ?
                    AND track_time = ?''',
                (tracking_data[0][0]['tracking_number'],
                 data[0]['trackdate'],
                 data[0]['tracktime']))
        existing = c.fetchone()

        if not existing:
            c.execute('''INSERT OR IGNORE INTO tracking_data
                        (tracking_number, status, place_name, place_code,
                         track_date, track_time, place_postcode, place_address,
                         place_lat, place_lng)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (tracking_data[0][0]['tracking_number'],
                     data[0]['status'],
                     data[0]['placeName'],
                     data[0]['placeCode'],
                     data[0]['trackdate'],
                     data[0]['tracktime'],
                     data[0]['placePostcode'],
                     data[0]['placeAddress'],
                     data[0]['placeLat'],
                     data[0]['placeLng']))

    # Delete old records if count exceeds 20
    c.execute('SELECT COUNT(*) FROM tracking_data')
    count = c.fetchone()[0]
    if count > 20:
        c.execute('''DELETE FROM tracking_data
                    WHERE id IN
                    (SELECT id FROM tracking_data
                    ORDER BY created_at ASC
                    LIMIT ?)''', (count - 20,))

    conn.commit()
