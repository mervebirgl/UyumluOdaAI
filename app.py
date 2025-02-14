from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
import joblib
import json
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()
origins = [
    "http://localhost",  # Yerel geliştirme için
    "http://127.0.0.1",  # Veya https://yourfrontenddomain.com
    "http://localhost:8000",
]
# 📌 CORS Ayarları (Güvenlik için belirli originleri tanımlayabilirsin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📌 Öğrenci Veri Modeli
class Student(BaseModel):
    name: str
    personality_vector: List[float]  # Liste elemanları float olarak belirlenmeli

class StudentRequest(BaseModel):
    student_id: int

# 📌 Veritabanı Bağlantısı
def create_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row  # Verileri dictionary formatında döndürmek için
    return conn

# 📌 Modeli Yükleme Fonksiyonu
def load_model():
    try:
        model, student_clusters = joblib.load("room_match_model.pkl")
        return model, student_clusters
    except FileNotFoundError:
        return None, None

# 📌 API Durumu Kontrolü
@app.get("/")
def home():
    return {"message": "Oda eşleştirme API'sine hoş geldiniz!"}

# 📌 Öğrenci Ekleme API'si
@app.post("/register_student")
def register_student(student: Student):
    conn = create_connection()
    cursor = conn.cursor()
    
    # JSON formatına çevir
    personality_vector_json = json.dumps(student.personality_vector)

    # Veritabanına ekleme
    try:
        cursor.execute(
            "INSERT INTO students (name, personality_vector) VALUES (?, ?)", 
            (student.name, personality_vector_json)
        )
        student_id = cursor.lastrowid  # Eklenen öğrencinin ID'sini al
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")
    finally:
        conn.close()

    return {"message": f"{student.name} başarıyla eklendi!", "student_id": student_id}

# 📌 Oda Eşleştirme API'si
@app.post("/match_room")
def match_room(data: StudentRequest):
    print(f"Alınan öğrenci ID: {data.student_id}")  # Log ekleyin
    student_id = data.student_id
    # Modeli yükle
    model, student_clusters = load_model()
    if model is None:
        raise HTTPException(status_code=500, detail="Model bulunamadı, önce eğitmelisin!")

    # Öğrencinin veritabanında olup olmadığını kontrol et
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    if not student:
        raise HTTPException(status_code=404, detail="Öğrenci veritabanında bulunamadı")

    # Eğer öğrenci modele dahil edilmişse, ona uygun odaları döndür
    if student_id in student_clusters:
        cluster = student_clusters[student_id]
        matching_students = [
            s_id for s_id, c in student_clusters.items() if c == cluster and s_id != student_id
        ]
        return {"student_id": student_id, "matching_students": matching_students}

    raise HTTPException(status_code=404, detail="Öğrenci modelde bulunamadı")











































