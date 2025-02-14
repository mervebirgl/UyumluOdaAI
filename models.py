import sqlite3
import json

def create_connection():
    """ Veritabanına bağlanır veya oluşturur. """
    conn = sqlite3.connect("database.db")
    return conn

def create_tables():
    """ Öğrenci ve oda tablolarını oluşturur. """
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            personality_vector TEXT,
            current_room_id INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number INTEGER NOT NULL,
            capacity INTEGER NOT NULL,
            students_in_room INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("✅ Veritabanı tabloları başarıyla oluşturuldu!")
