import sqlite3
import numpy as np
from sklearn_extra.cluster import KMedoids
import joblib

def get_students():
    """Veritabanından öğrenci verilerini çeker."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15 FROM students")
    students = cursor.fetchall()
    conn.close()

    student_data = []
    student_ids = []
    for student in students:
        s_id = student[0]  # İlk eleman öğrenci ID'si
        responses = list(student[1:])  # Geri kalanlar kişilik vektörü (q1 - q15)
        student_ids.append(s_id)
        student_data.append(responses)

    return np.array(student_data), student_ids

def train_kmedoids(n_clusters=5):
    """Öğrenci kişilik testleri ile K-Medoids modelini eğitir ve öğrenci ID'leriyle eşleşme yapar."""
    data, student_ids = get_students()

    if len(data) < n_clusters:
        print("Yeterli veri yok, model eğitilemiyor.")
        return

    # K-Medoids modeli eğitme
    kmedoids = KMedoids(n_clusters=n_clusters, random_state=42, method="pam")
    kmedoids.fit(data)

    # Öğrenci kümelerini belirleme
    student_clusters = {student_ids[i]: int(kmedoids.labels_[i]) for i in range(len(student_ids))}

    # Modeli kaydet
    joblib.dump((kmedoids, student_clusters), "room_match_model.pkl")
    print("✅ K-Medoids modeli başarıyla eğitildi ve kaydedildi!")

if __name__ == "__main__":
    train_kmedoids()
