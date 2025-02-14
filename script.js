document.addEventListener("DOMContentLoaded", function () {
    const API_URL = "http://127.0.0.1:8000/register_student"; 
    const MATCH_URL = "http://127.0.0.1:8000/match_room"; 

    const testContainer = document.getElementById("test-container");
    const testForm = document.getElementById("testForm");
    const resultDiv = document.getElementById("roomResult");
    const submitButton = testForm.querySelector("button[type='submit']");

    const questions = [
        { name: "extraversion", text: "Dışadönüklük" },
        { name: "agreeableness", text: "Uyumluluk" },
        { name: "conscientiousness", text: "Sorumluluk" },
        { name: "openness", text: "Açıklık" },
        { name: "neuroticism", text: "Duygusal Denge" }
    ];

    function renderQuestions() {
        questions.forEach(q => {
            const questionGroup = document.createElement("div");
            questionGroup.classList.add("test-group");

            questionGroup.innerHTML = `
                <label class="form-label">${q.text}</label>
                <div class="btn-group d-flex">
                    ${[1, 2, 3, 4, 5].map(i => `
                        <input type="radio" class="btn-check" name="${q.name}" id="${q.name}-${i}" value="${i}" required>
                        <label class="btn btn-outline-primary flex-fill small-btn" for="${q.name}-${i}">${i}</label>
                    `).join("")}
                </div>
            `;

            testContainer.appendChild(questionGroup);
        });
    }

    async function handleFormSubmit(event) {
        event.preventDefault();

        const fullName = testForm.full_name.value.trim();
        if (!fullName) {
            resultDiv.innerHTML = "<p style='color: red;'>Lütfen adınızı ve soyadınızı giriniz.</p>";
            return;
        }

        submitButton.innerHTML = "İşleniyor...";
        submitButton.disabled = true;

        let jsonData = {
            name: fullName,
            personality_vector: questions.map(q => parseInt(document.querySelector(`input[name="${q.name}"]:checked`).value))
        };

        try {
            const response = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(jsonData)
            });

            if (!response.ok) {
                throw new Error(`Hata: ${response.statusText}`);
            }

            const responseData = await response.json();
            console.log("Öğrenci Eklendi:", responseData);

            // Backend'den öğrenci kimliği çekilecek
            const studentId = responseData.student_id; 

            // Şimdi oda eşleşmesini başlat
            await matchRoom(studentId);

        } catch (error) {
            console.error("Hata:", error);
            resultDiv.innerHTML = "<p style='color: red;'>Sunucuya bağlanılamadı!</p>";
        } finally {
            submitButton.innerHTML = "Gönder";
            submitButton.disabled = false;
        }
    }

    async function matchRoom(studentId) {
        try {
            const response = await fetch(MATCH_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ student_id: studentId })
            });

            if (!response.ok) {
                throw new Error(`Hata: ${response.statusText}`);
            }

            const data = await response.json();
            console.log("Oda Eşleşmesi:", data);

            resultDiv.innerHTML = `<h5>Önerilen Öğrenciler:</h5>`;
            if (data.matching_students.length > 0) {
                resultDiv.innerHTML += `<ul class="room-list">` +
                    data.matching_students.map(s_id => `<li>Öğrenci ID: ${s_id}</li>`).join("") +
                    `</ul>`;
            } else {
                resultDiv.innerHTML += "<p>Eşleşen öğrenci bulunamadı.</p>";
            }

        } catch (error) {
            console.error("Hata:", error);
            resultDiv.innerHTML = "<p style='color: red;'>Oda eşleşmesi yapılamadı.</p>";
        }
    }

    renderQuestions();
    testForm.addEventListener("submit", handleFormSubmit);
});
