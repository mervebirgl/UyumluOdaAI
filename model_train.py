import sqlite3
import json
import numpy as np
from sklearn.cluster import KMeans
import joblib

def get_students():
    """Veritabanından öğrenci verilerini çeker."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, personality_vector FROM students")
    students = cursor.fetchall()
    conn.close()

    student_data = []
    student_ids = []
    
    for s_id, vec in students:
        student_ids.append(s_id)
        try:
            # JSON'u çözümle
            vec = json.loads(vec)

            # Kişilik vektörünün düzgün boyutta olduğundan emin ol (4 elemanlı)
            if len(vec) == 4:  # Şimdi 4 elemanlı vektörleri kabul ediyoruz
                student_data.append(vec)
            else:
                print(f"Geçersiz vektör: {vec} (id: {s_id})")
        except json.JSONDecodeError:
            print(f"JSON çözümleme hatası (id: {s_id})")

    return np.array(student_data), student_ids

def train_kmeans(n_clusters=3):
    """Öğrenci kişilik testleri ile K-Means modelini eğitir ve öğrenci ID'leriyle eşleşme yapar."""
    data, student_ids = get_students()

    if len(data) < n_clusters:
        print("Yeterli veri yok, model eğitilemiyor.")
        return

    # Geçerli veriler ile KMeans modelini eğit
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(data)

    # Öğrenci kümelerini almak
    student_clusters = {}
    for i in range(len(student_ids)):
        # labels_ ve student_ids uzunlukları uyumlu
        if i < len(kmeans.labels_):
            student_clusters[student_ids[i]] = int(kmeans.labels_[i])
        else:
            print(f"Uygunsuz indeks: {i}, labels_ boyutu daha küçük")

    # Modeli kaydet
    joblib.dump((kmeans, student_clusters), "room_match_model.pkl")
    print("✅ Model başarıyla eğitildi ve kaydedildi!")

if __name__ == "__main__":
    train_kmeans()
