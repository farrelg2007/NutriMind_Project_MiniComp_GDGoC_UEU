import os
import re
import json
import time
import warnings
from flask import Flask, render_template, request, jsonify

warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai

app = Flask(__name__)

API_KEY = "AIzaSyBEmbQm6uISrWmGQfPNS5OPD0wJJRyYjxk"
genai.configure(api_key=API_KEY)

CACHED_WORKING_MODEL = None


def extract_json_from_text(text):
    """
    Membersihkan teks respons dari AI dan mengonversinya menjadi objek JSON.
    Menggunakan algoritma Balanced Stack-based Parser yang sangat kuat untuk memisahkan
    dan mengisolasi blok JSON yang valid, terlepas dari adanya teks basa-basi,
    markdown, backticks, koma gantung, maupun duplikasi blok JSON dari model AI.
    """
    try:
        cleaned_text = text.strip()
        
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(cleaned_text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                if brace_count > 0:
                    brace_count -= 1
                    if brace_count == 0:
                        potential_json = cleaned_text[start_idx:i + 1]
                        potential_json = re.sub(r',\s*([\]}])', r'\1', potential_json)
                        potential_json = re.sub(r'[\x00-\x1F\x7F]', '', potential_json)
                        
                        try:
                            return json.loads(potential_json)
                        except Exception:
                            pass

        json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', cleaned_text, re.DOTALL)
        for block in json_blocks:
            try:
                block_clean = re.sub(r',\s*([\]}])', r'\1', block)
                block_clean = re.sub(r'[\x00-\x1F\x7F]', '', block_clean)
                return json.loads(block_clean)
            except Exception:
                pass

        start_idx = cleaned_text.find('{')
        end_idx = cleaned_text.rfind('}')
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            fallback_str = cleaned_text[start_idx:end_idx + 1]
            fallback_str = re.sub(r',\s*([\]}])', r'\1', fallback_str)
            fallback_str = re.sub(r'[\x00-\x1F\x7F]', '', fallback_str)
            return json.loads(fallback_str)

        raise ValueError("Tidak mendeteksi adanya struktur data JSON yang valid di dalam respons AI.")

    except Exception as e:
        print(f"[Error Parsing JSON]: {e}\nTeks asli dari Gemini:\n{text}")
        raise ValueError(f"Gagal memformat data gizi dari AI: {str(e)}")


def resolve_best_model():
    """
    Mendeteksi secara dinamis model apa saja yang aktif dan didukung oleh API Key pengguna.
    Ini menghindari error 404 jika akun atau API Key memiliki batasan model tertentu.
    """
    global CACHED_WORKING_MODEL
    
    if CACHED_WORKING_MODEL:
        try:
            # Validate cached model is still available and supports generation
            for m in genai.list_models():
                clean_name = m.name.replace('models/', '')
                methods = getattr(m, 'supported_generation_methods', None)
                if clean_name == CACHED_WORKING_MODEL and methods and 'generateContent' in methods:
                    return [CACHED_WORKING_MODEL]
            CACHED_WORKING_MODEL = None
        except Exception:
            # If we can't list models, clear cached model to force fallback candidates
            CACHED_WORKING_MODEL = None

    # Prefer a known-working flash model from the user's API key output,
    # falling back to other recent flash models.
    candidates = [
        'gemini-flash-latest',
        'gemini-3.5-flash',
        'gemini-3-flash-preview',
        'gemini-2.5-flash',
        'flash-preview',
    ]
    
    try:
        print("[NutriMind Debug]: Memindai model aktif pada API Key Anda...")
        available_models = []
        for m in genai.list_models():
            methods = getattr(m, 'supported_generation_methods', None)
            if methods and 'generateContent' in methods:
                clean_name = m.name.replace('models/', '')
                available_models.append(clean_name)

        print(f"[NutriMind Debug]: Model yang mendukung generateContent: {available_models}")

        # Prioritize models that include 'flash' or 'preview' in their names
        prioritized = [m for m in available_models if ('flash' in m or 'preview' in m)]
        for m in available_models:
            if m not in prioritized:
                prioritized.append(m)

        if prioritized:
            return prioritized
    except Exception as e:
        print(f"[NutriMind Debug]: Gagal memindai model secara dinamis ({e}). Menggunakan metode fallback manual.")

    # Fallback candidates if listing fails or nothing usable found
    return [
        'gemini-flash-latest',
        'gemini-3.5-flash',
        'gemini-3-flash-preview',
        'gemini-2.5-flash',
        'flash-preview',
    ]


@app.route('/')
def home():
    """Menampilkan halaman utama aplikasi NutriMind."""
    try:
        return render_template('index.html')
    except Exception as e:
        return (
            f"<h3>Error: Pastikan file 'index.html' berada di dalam folder "
            f"bernama 'templates'</h3><br>Detail: {str(e)}"
        ), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Endpoint utama: Menerima jurnal pengguna dan mood dari frontend,
    mengirimkannya ke Gemini dengan sistem instruksi terstruktur,
    dan mengembalikan data JSON terstruktur yang cocok dengan index.html.
    """
    global CACHED_WORKING_MODEL
    data = request.get_json()

    if not data or not data.get('journal'):
        return jsonify({"error": "Jurnal tidak boleh kosong."}), 400

    journal_text = data['journal'].strip()
    mood = data.get('mood', 'Netral')

    if len(journal_text) < 10:
        return jsonify({"error": "Ceritakan lebih detail ya, minimal 10 karakter."}), 400

    try:
        system_prompt = (
            "Anda adalah NutriMind AI, ahli gizi dan wellness coach yang ramah, hangat, dan suportif.\n"
            "Tugas Anda adalah menganalisis keluhan fisik, mood, dan makanan harian pengguna.\n"
            "Gunakan bahasa Indonesia yang empatik, santai, dan mudah dimengerti.\n\n"
            "Anda WAJIB memberikan respons HANYA dalam format JSON mentah tanpa backtick (```), tanpa markdown, "
            "dan tanpa penjelasan teks tambahan di luar blok JSON tersebut.\n"
            "Struktur JSON Anda harus persis seperti template berikut:\n"
            "{\n"
            '  "ringkasan": "Ulasan singkat 1-2 kalimat bernada hangat tentang kondisi mereka hari ini.",\n'
            '  "skor_nutrisi": 70,\n'
            '  "kalori_estimasi": "~1500 kkal",\n'
            '  "kekurangan": [\n'
            '    {\n'
            '      "nutrisi": "Nama Zat Gizi/Nutrisi",\n'
            '      "dampak": "Mengapa kekurangan zat ini memicu keluhan fisik yang ditulis user.",\n'
            '      "icon": "Emoji yang relevan"\n'
            '    }\n'
            '  ],\n'
            '  "insight": "Penjelasan edukatif ringan menghubungkan makanan dengan keluhan fisik.",\n'
            '  "saran_makanan": [\n'
            '    {\n'
            '      "nama": "Nama Makanan Alternatif Sehat",\n'
            '      "alasan": "Mengapa makanan ini membantu memulihkan energi/kondisi user.",\n'
            '      "mudah_didapat": true\n'
            '    }\n'
            '  ],\n'
            '  "pesan_motivasi": "Satu kalimat penyemangat hangat agar mereka terus menjaga pola makan sehat."\n'
            "}"
        )

        user_prompt = (
            f"Kondisi Mood Pengguna: {mood}\n"
            f"Catatan Konsumsi & Kondisi Tubuh Pengguna:\n\"{journal_text}\""
        )

        model_candidates = resolve_best_model()
        response = None
        last_exception = None

        max_retries = 2
        retry_delays = [1]

        for model_name in model_candidates:
            success = False
            for attempt in range(max_retries):
                try:
                    print(f"[NutriMind]: Mengirim ke Gemini ({model_name}) - Percobaan ke-{attempt + 1}...")
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    response = model.generate_content([system_prompt, user_prompt])
                    
                    if response and response.text:
                        print(f"[NutriMind]: Sukses menggunakan model {model_name}!")
                        CACHED_WORKING_MODEL = model_name
                        success = True
                        break
                except Exception as ex:
                    last_exception = ex
                    err_str = str(ex)
                    
                    if any(err in err_str for err in ["400", "403", "404", "INVALID_ARGUMENT", "PERMISSION_DENIED", "NOT_FOUND"]):
                        break
                    
                    if attempt < max_retries - 1:
                        sleep_time = retry_delays[attempt]
                        time.sleep(sleep_time)
            
            if success:
                break

        if not response:
            raise last_exception if last_exception else Exception("Semua kandidat model Gemini gagal diakses.")
        
        parsed_result = extract_json_from_text(response.text)
        return jsonify(parsed_result)

    except Exception as e:
        error_msg = str(e)
        print(f"[NutriMind Server Error]: {error_msg}")
        
        if "503" in error_msg or "overloaded" in error_msg.lower():
            return jsonify({
                "error": "Server Google Gemini saat ini sedang sangat sibuk (Error 503). Sistem telah mencoba mengirim ulang otomatis tetapi server masih belum merespon. Mohon kirimkan ulang kembali dalam beberapa detik."
            }), 503
        elif "404" in error_msg or "not found" in error_msg.lower():
            return jsonify({
                "error": "Layanan Gemini tidak dapat mendeteksi model yang kompatibel pada API Key Anda. Pastikan API Key dibuat langsung melalui Google AI Studio."
            }), 404
        return jsonify({"error": f"Terjadi kendala saat menganalisis data: {error_msg}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)