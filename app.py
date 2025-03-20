import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

app = FastAPI()

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8000",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StudentRequest(BaseModel):
    student_id: int
    new_room_id: int = None

def create_connection():
    """Veritabanı bağlantısını oluşturur."""
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def load_model():
    """K-Medoids modelini yükler."""
    try:
        model, student_clusters = joblib.load("room_match_model.pkl")
        return model, student_clusters
    except FileNotFoundError:
        return None, None

@app.get("/")
def home():
    return {"message": "Oda eşleştirme API'sine hoş geldiniz!"}

@app.post("/match_room")
def match_room(data: StudentRequest):
    student_id = data.student_id
    model, student_clusters = load_model()

    if model is None:
        raise HTTPException(status_code=500, detail="Model bulunamadı, önce eğitmelisin!")

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        raise HTTPException(status_code=404, detail="Öğrenci bulunamadı")

    if student_id in student_clusters:
        cluster = student_clusters[student_id]
        matching_students = [s_id for s_id, c in student_clusters.items() if c == cluster and s_id != student_id]

        cursor.execute("SELECT * FROM rooms WHERE current_capacity < max_capacity")
        available_rooms = cursor.fetchall()

        recommended_rooms = []
        for room in available_rooms:
            room_id = room["room_id"]
            
            # Öğrenci ile eşleşen odadaki öğrencileri sayarak uyum oranını hesapla
            if matching_students:
                query = "SELECT COUNT(*) FROM students WHERE room_id = ? AND student_id IN ({})".format(
                    ",".join(map(str, matching_students)))
                cursor.execute(query, (room_id,))
                match_count = cursor.fetchone()[0]
            else:
                match_count = 0

            total_students = cursor.execute("SELECT COUNT(*) FROM students WHERE room_id = ?", (room_id,)).fetchone()[0]
            
            # Uyum oranı hesapla
            match_percentage = (match_count / max(total_students, 1)) * 100  # Sıfıra bölünmeyi önlemek için
            recommended_rooms.append({"room_id": room_id, "match_percentage": round(match_percentage, 2)})

        recommended_rooms.sort(key=lambda x: x["match_percentage"], reverse=True)
        conn.close()
        return {"student_id": student_id, "recommended_rooms": recommended_rooms[:2]}

    conn.close()
    raise HTTPException(status_code=404, detail="Öğrenci modelde bulunamadı")

@app.post("/confirm_room_change")
def confirm_room_change(data: StudentRequest):
    student_id = data.student_id
    new_room_id = data.new_room_id

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        raise HTTPException(status_code=404, detail="Öğrenci bulunamadı")

    cursor.execute("UPDATE students SET room_id = ? WHERE student_id = ?", (new_room_id, student_id))
    cursor.execute("UPDATE rooms SET current_capacity = current_capacity + 1 WHERE room_id = ?", (new_room_id,))
    cursor.execute("UPDATE rooms SET current_capacity = current_capacity - 1 WHERE room_id = ?", (student["room_id"],))
    conn.commit()
    conn.close()

    return {"message": "Oda değişikliği başarılı!", "new_room_id": new_room_id}
