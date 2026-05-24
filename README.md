# 🥗 NutriMind — AI Food Journal & Wellness Tracker

> Mini Competition (Minicomp) GDGoC Universitas Esa Unggul
> Tema: "Build Impactful Solutions with Artificial Intelligence"

---

## 💡 Tentang Proyek

**NutriMind** adalah aplikasi web pencatat makanan harian yang menghubungkan
nutrisi dengan kondisi fisik dan suasana hati pengguna.

Pengguna cukup mengetik secara bebas apa yang mereka makan hari ini dan
bagaimana kondisi tubuh mereka. **Gemini 1.5 Flash** akan menganalisis pola
tersebut dan memberikan:

- 📊 Skor nutrisi harian (1–100)
- ⚠️ Kekurangan nutrisi beserta dampaknya pada tubuh
- 🧠 Insight yang menghubungkan makanan dengan kondisi fisik
- 🥦 Saran makanan pengganti yang lebih sehat & mudah didapat
- 💪 Pesan motivasi yang personal

---

## 🛠️ Teknologi

| Teknologi          | Kegunaan                        |
|--------------------|---------------------------------|
| Python 3.8+        | Runtime backend                 |
| Flask              | Web framework                   |
| Gemini 1.5 Flash   | Analisis teks nutrisi (AI)      |
| Tailwind CSS       | Styling responsif               |
| HTML + CSS + JS    | Frontend UI                     |

---

## 📁 Struktur Folder

```
nutrimind-v2/
├── app.py               ← Backend Flask
├── package.json         ← Dependensi Node.js (Tailwind CSS)
├── templates/
│   └── index.html       ← Seluruh UI dalam 1 file
└── static/
    ├── css/
    │   ├── input.css    ← Tailwind source
    │   └── main.css     ← Custom styles + tokens
    └── js/
        └── main.js      ← Frontend logic
```

---

## 🚀 Cara Menjalankan

### 1. Setup Virtual Environment

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Linux / Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependensi Python
```bash
pip install google-generativeai Flask Pillow
```

### 3. Install Dependensi Node.js (Tailwind CSS)
```bash
npm install
```

### 4. Setup API Key
Buka `app.py`, cari baris ini (baris ~14):
```python
API_KEY = "MASUKKAN_API_KEY_KAMU"
```
Ganti dengan API Key baru dari: https://aistudio.google.com/


### 5. Jalankan Server
```bash
python app.py
```

### 6. Buka di Browser / HP Android
- **Laptop:** `http://localhost:5000`
- **HP Android (WiFi sama):**
  - **Windows:** Buka CMD, ketik `ipconfig` → cari "IPv4 Address"
  - **Linux:** Ketik `hostname -I` atau `ip addr show`
  - Buka di HP: `http://[IP_LAPTOP]:5000`

---

## 🔌 Alur Kerja

```
User ketik jurnal makanan + kondisi tubuh
           │
           ▼ POST /analyze (JSON)
      Flask app.py
           │
           ▼ Prompt + teks ke Gemini API
    Gemini 1.5 Flash
           │
           ▼ JSON: skor, insight, kekurangan, saran
      Flask → response
           │
           ▼
   index.html menampilkan hasil
```

---

## 👥 Tim

| Nama                    | Peran                          |
|-------------------------|--------------------------------|
| Farrel Gian             | Backend Flask + Gemini API     |
| Bimo Rajendra Fassah    | UI/UX (index.html)             |
