import streamlit as st
import random
import requests
import time
from datetime import datetime

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxfcOZUB5oUS74pQvoLFOsYD2SWfFwlHhgJkviawY1m56SVthIf1Qszxo4Zb3koCsEe/exec"

st.set_page_config(
    page_title="Studi Memori Kerja",
    layout="centered"
)

# ---------------------------------------------------------
# CSS STYLING (DIUPDATE UNTUK KONSISTENSI GRID STREAMLIT)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* 1. KOTAK JAWABAN (Tombol Biasa/Secondary) */
    div.stButton > button {
        width: 100%;
        aspect-ratio: 1 / 1; 
        border-radius: 8px;
        border: 2px solid #CBD5E0;
        background-color: #EDF2F7;
        padding: 0;
        transition: all 0.1s;
        /* Hapus semua transformasi untuk mencegah layout shift saat klik */
        transform: none !important; 
        /* Tambahan: Menghilangkan margin bawaan Streamlit agar kotak lebih rapat */
        margin: 0 !important; 
    }
    
    /* Efek Hover di Kotak Jawaban */
    div.stButton > button:hover {
        border-color: #3182CE;
        background-color: #EBF8FF;
        transform: none; 
    }

    /* FEEDBACK HIJAU INSTAN TANPA LAYOUT SHIFT (saat tombol ditekan) */
    div.stButton > button:active {
        background-color: #48BB78 !important; /* Hijau saat ditekan */
        color: white;
        box-shadow: 0 0 10px rgba(72, 187, 120, 0.5);
    }

    /* 2. TOMBOL NAVIGASI (Mulai, Lanjut, dll) */
    div.stButton > button[kind="primary"] {
        aspect-ratio: unset !important;
        width: auto !important;
        min-width: 120px;
        padding: 0.5rem 1rem;
        background-color: #FF4B4B;
        border: none;
        color: white;
        transform: none; 
    }
    
    div.stButton > button[kind="primary"]:hover {
        background-color: #FF2B2B;
        transform: none;
    }

    /* 3. GRID HTML MANUAL (Untuk Fase Soal/Blink) */
    .corsi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        width: 100%;
    }
    .corsi-box {
        aspect-ratio: 1 / 1;
        border-radius: 8px;
        background: #EDF2F7;
        border: 2px solid #CBD5E0;
    }
    
    /* Warna Biru (Soal) */
    .corsi-active-blue {
        background: #3182CE !important;
        border-color: #2B6CB0;
        box-shadow: 0 0 15px rgba(49, 130, 206, 0.5);
    }
    
    /* Tambahan: Mengurangi margin/padding di antara st.columns agar terlihat seperti grid */
    div[data-testid^="stHorizontalBlock"] > div[data-testid^="stColumn"] {
        padding-left: 0.25rem !important;
        padding-right: 0.25rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# FUNGSI BARU UNTUK MERENDER GRID TOMBOL STREAMLIT 4X4
# ---------------------------------------------------------
def render_corsi_grid_buttons(positions):
    """Merender grid 4x4 menggunakan st.columns dan st.button. 
    Mengembalikan posisi (pos_val) yang diklik jika berada di fase 'input'."""
    clicked_pos = None
    
    # Gunakan wadah yang konsisten
    with st.container():
        for row in range(4):
            row_cols = st.columns(4) 
            for col in range(4):
                idx = row * 4 + col
                pos_val = positions[idx]
                
                # Base key harus stabil
                key_base = f"btn_grid_{pos_val}" 
                
                if st.session_state.corsi["status"] == "input":
                    # Fase Input: Tombol aktif, key harus unik per klik untuk memaksa rerender
                    key_final = f"{key_base}_input_{len(st.session_state.corsi['user_clicks'])}"
                    if row_cols[col].button(" ", key=key_final):
                        clicked_pos = pos_val
                else:
                    # Fase Idle: Tombol dinonaktifkan (hanya tampilan), key stabil
                    row_cols[col].button(" ", key=f"{key_base}_idle", disabled=True)
                    
    return clicked_pos

# ---------------------------------------------------------
# DATA & HELPERS (render_grid_html & blink_sequence tetap menggunakan HTML)
# ---------------------------------------------------------
# ... (send_to_webhook, generate_positions, generate_sequence, render_grid_html, blink_sequence tidak berubah) ...

# Salin fungsi generate_positions, generate_sequence, render_grid_html, dan blink_sequence
# dari kode asli Anda ke sini agar kode ini bisa berjalan.

def generate_positions():
    pos = list(range(1, 17))
    random.shuffle(pos)
    return pos

def generate_sequence(level):
    # Level 1 (cs['level']=1) akan menghasilkan sequence 2 (1+1)
    return random.sample(range(1, 17), level + 1)

def render_grid_html(positions, active=None, color_mode="blue"):
    # Fungsi ini hanya digunakan di fase BLINK
    html = '<div class="corsi-grid">'
    for p in positions:
        extra_class = ""
        if p == active:
            extra_class = "corsi-active-green" if color_mode == "green" else "corsi-active-blue"
        html += f'<div class="corsi-box {extra_class}"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def blink_sequence(sequence, positions, container):
    # Fungsi ini hanya digunakan di fase BLINK
    with container:
        render_grid_html(positions, active=None)
    time.sleep(1)

    for pid in sequence:
        with container:
            render_grid_html(positions, active=pid, color_mode="blue")
        time.sleep(0.7)
        
        with container:
            render_grid_html(positions, active=None)
        time.sleep(0.3)


# ---------------------------------------------------------
# HALAMAN 3: TES CORSI (DIUPDATE)
# ---------------------------------------------------------
def render_corsi():
    st.header("🧠 Bagian 2 — Tes Corsi")

    if "corsi" not in st.session_state:
        st.session_state.corsi = {
            "level": 1, "positions": None, "sequence": None,
            "user_clicks": [], "attempt": 1, "results": {}, "status": "idle"
        }
    cs = st.session_state.corsi

    if cs["positions"] is None:
        cs["positions"] = generate_positions()
        # cs["level"]=1 -> generate_sequence(1) -> 2 kotak (Sesuai Gambar 1)
        cs["sequence"] = generate_sequence(cs["level"])
        cs["user_clicks"] = []
        cs["status"] = "idle"

    col_left, col_game, col_right = st.columns([1, 3, 1])

    with col_game:
        # 1. FASE PERSIAPAN (IDLE)
        if cs["status"] == "idle":
            st.info(f"Level {cs['level']} | Ingat {len(cs['sequence'])} kotak")
            
            # --- PERBAIKAN: Gunakan tombol Streamlit yang sudah di-style ---
            render_corsi_grid_buttons(cs["positions"])
            
            if st.button("Mulai Level Ini", type="primary", use_container_width=True):
                cs["status"] = "blink"
                st.rerun()
            return False

        # 2. FASE SOAL (BLINK)
        if cs["status"] == "blink":
            grid_placeholder = st.empty()
            # Tetap gunakan blink_sequence (HTML) untuk animasi
            blink_sequence(cs["sequence"], cs["positions"], grid_placeholder)
            
            cs["status"] = "input"
            st.rerun()
            return False

        # 3. FASE JAWABAN (INPUT)
        if cs["status"] == "input":
            st.write("👉 Klik sesuai urutan:")
            
            # --- PERBAIKAN: Gunakan fungsi helper untuk rendering dan menangkap klik ---
            clicked_pos = render_corsi_grid_buttons(cs["positions"])

            # --- LOGIKA KLIK ---
            if clicked_pos is not None:
                cs["user_clicks"].append(clicked_pos)
                st.rerun()

            # --- CEK JAWABAN ---
            if len(cs["user_clicks"]) == len(cs["sequence"]):
                if cs["user_clicks"] == cs["sequence"]:
                    cs["results"][f"Level_{cs['level']}"] = 1
                    cs["level"] += 1
                    cs["positions"] = None
                    cs["attempt"] = 1
                    st.success("Benar! Lanjut...")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    if cs["attempt"] == 1:
                        cs["attempt"] = 2
                        cs["user_clicks"] = []
                        st.warning("Salah urutan. Coba lagi.")
                        time.sleep(1.5)
                        cs["status"] = "blink"
                        st.rerun()
                    else:
                        cs["results"][f"Level_{cs['level']}"] = 0
                        cs["status"] = "finished"
                        st.error("Game Over.")
                        return True

    return False
    
# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
# ... (render_identity_form, render_questionnaire, dan main() tidak berubah) ...
# Salin fungsi render_identity_form, render_questionnaire, dan main()
# dari kode asli Anda ke sini agar kode ini bisa berjalan.

def render_identity_form():
    # ... (Isi dari render_identity_form) ...
    st.header("Data Responden")
    st.info("Formulir Data Responden (Mock)")
    if 'identity_completed' not in st.session_state:
        st.session_state.identity_completed = False
        st.session_state.identity_data = {}
    
    inisial = st.text_input("Inisial (wajib)", "A")
    umur = st.number_input("Umur", min_value=17, max_value=80, step=1, value=25)
    gender = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"], index=0)
    pendidikan = st.selectbox("Pendidikan", ["Pilih...", "SMA/SMK", "D3", "S1/Sederajat"], index=2)
    kota = st.text_input("Domisili (Kota/Kabupaten)", "Surabaya")
    durasi = st.selectbox("Durasi layar/hari", ["Pilih...", "< 1 jam", "1–2 jam", "2–4 jam", "4–6 jam", "> 6 jam"], index=4)
    aktivitas = st.selectbox("Aktivitas utama", ["Pilih...", "Belajar", "Media sosial", "Game", "Menonton video", "Lainnya"], index=3)
    sebelum_tidur = st.radio("Gawai sebelum tidur?", ["Ya", "Tidak"], index=0)
    kualitas_tidur = st.selectbox("Kualitas tidur", ["Pilih...", "Baik", "Sedang", "Buruk"], index=1)
    durasi_tidur = st.selectbox("Durasi tidur", ["Pilih...", "< 5 jam", "5–6 jam", "6–8 jam", "> 8 jam"], index=2)
    gangguan = st.selectbox("Riwayat gangguan fokus", ["Pilih...", "Tidak ada", "ADHD", "Slow learner", "Lainnya"], index=1)
    kesehatan = st.selectbox("Riwayat kesehatan kognitif", ["Pilih...", "Tidak ada", "Cedera kepala", "Riwayat kejang", "Obat fokus"], index=0)
    kafein = st.selectbox("Konsumsi kafein", ["Pilih...", "Tidak pernah", "1x sehari", "2x sehari", "3x atau lebih"], index=1)


    if st.button("Lanjut ke Kuesioner", type="primary"):
        if inisial.strip() == "" or pendidikan == "Pilih..." or kota.strip() == "":
            st.error("Lengkapi semua data wajib.")
        else:
            st.session_state.identity_completed = True
            st.session_state.identity_data = {
                "inisial": inisial, "umur": int(umur), "jenis_kelamin": gender,
                "pendidikan": pendidikan, "kota": kota, "durasi_layar": durasi,
                "aktivitas_gawai": aktivitas, "sebelum_tidur": sebelum_tidur,
                "kualitas_tidur": kualitas_tidur, "durasi_tidur": durasi_tidur,
                "riwayat_gangguan_fokus": gangguan, "riwayat_kesehatan": kesehatan, "kafein": kafein
            }
            st.rerun()

QUESTIONS = [
    "Saya bermain internet lebih lama dari yang saya rencanakan.",
    "Saya membentuk pertemanan baru melalui internet.",
    "Saya merahasiakan aktivitas saya di internet dari orang lain.",
    "Saya menutupi pikiran yang mengganggu dengan memikirkan hal menyenangkan tentang internet.",
    "Saya takut hidup tanpa internet akan membosankan atau kosong.",
    "Saya marah jika ada yang mengganggu saat saya bermain internet.",
    "Saya terus memikirkan internet ketika tidak sedang bermain.",
    "Saya lebih memilih internet daripada beraktivitas dengan orang lain.",
    "Saya merasa gelisah jika tidak bermain internet, dan tenang kembali setelah bermain.",
    "Saya mengabaikan pekerjaan rumah demi bermain internet.",
    "Waktu belajar atau nilai akademik saya menurun akibat internet.",
    "Kinerja saya di sekolah/rumah terganggu karena internet.",
    "Saya sering kurang tidur karena bermain internet.",
    "Saya berusaha mengurangi waktu internet tetapi gagal.",
    "Saya sering berkata 'sebentar lagi' saat bermain internet.",
    "Saya berusaha menyembunyikan durasi bermain internet.",
    "Saya mengabaikan kegiatan penting demi internet.",
    "Saya merasa sulit berhenti ketika sedang bermain internet."
]

def render_questionnaire():
    st.header("Bagian 1 — IAT")
    answers = {}
    st.info("Pilih 1 (Tidak Pernah) hingga 4 (Selalu)")
    for i, q in enumerate(QUESTIONS, 1):
        answers[f"Q{i}"] = st.radio(f"{i}. {q}", [1, 2, 3, 4], horizontal=True, key=f"q{i}", index=0)

    if st.button("Selesai → Tes Corsi", type="primary"):
        st.session_state.answers = answers
        st.session_state.questionnaire_done = True
        st.rerun()

def send_to_webhook(payload):
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        return r.status_code == 200, r.status_code
    except Exception as e:
        return False, str(e)


def main():
    st.title("Studi Kognitif")

    if st.session_state.get("thankyou", False):
        st.success("Terima kasih. Data tersimpan.")
        if st.button("Reset", type="primary"):
            st.session_state.clear()
            st.rerun()
        return

    if not st.session_state.get("identity_completed", False):
        render_identity_form()
        return

    if not st.session_state.get("questionnaire_done", False):
        render_questionnaire()
        return

    finished = render_corsi()

    if finished:
        cs = st.session_state.corsi
        
        passed = [int(k.split("_")[1]) for k, v in cs["results"].items() if v == 1]
        max_lvl = max(passed) if passed else 0

        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_iat": sum(st.session_state.answers.values()),
            "corsi_max_level": max_lvl
        }
        payload.update(st.session_state.identity_data)
        payload.update(st.session_state.answers)
        payload.update(cs["results"])

        with st.spinner("Menyimpan data..."):
            ok, info = send_to_webhook(payload)
        
        if ok:
            st.session_state.thankyou = True
            st.rerun()
        else:
            st.error(f"Gagal kirim data ({info}).")
            if st.button("Coba Lagi", type="primary"):
                st.rerun()

if __name__ == "__main__":
    main()
