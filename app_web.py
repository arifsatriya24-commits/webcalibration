import streamlit as st
import pandas as pd
import os
import base64

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Develop Arif - Calibration", layout="wide")

# --- FUNGSI LOGO LOGIN ---
def get_base64_logo(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def tampilkan_logo_login():
    nama_file_logo = "logo.png" 
    if os.path.exists(nama_file_logo):
        logo_base64 = get_base64_logo(nama_file_logo)
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="200"></div>', unsafe_allow_html=True)

# 2. WATERMARK
st.markdown("<style>.footer {position: fixed; right: 20px; bottom: 10px; color: grey; font-size: 14px; font-style: italic; z-index: 100;}</style><div class='footer'>Developed by Arif Satriya</div>", unsafe_allow_html=True)

# --- 3. DATABASE SESSION STATE (KUNCI AGAR DATA TIDAK HILANG) ---
if 'database_alat' not in st.session_state:
    st.session_state.database_alat = {}

# --- 4. LOGIN ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    tampilkan_logo_login()
    st.markdown("<h1 style='text-align: center;'>🔐 Portal Calibration Security</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Masuk"):
            if user == "arif" and password == "000":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Login Gagal!")
    st.stop()

# --- 5. DASHBOARD UTAMA ---
st.title("🛡️ Hasil Evaluasi Kalibrasi")

with st.sidebar:
    if st.button("🚪 Keluar Sistem"):
        st.session_state.authenticated = False
        st.rerun()
    
    st.markdown("---")
    st.header("➕ Tambah Evaluasi")
    nama_input = st.text_input("Nama Alat (Misal: TLC002)")
    sn_input = st.text_input("Nomor Seri")
    satuan = st.selectbox("Satuan Alat", ["mm", "rpm", "kg", "celcius"])
    toleransi_default = st.number_input(f"Batas Toleransi Default ({satuan})", value=0.50)
    file_csv = st.file_uploader("Upload Data CSV", type="csv")
    
    if st.button("Simpan Hasil Evaluasi"):
        if file_csv and nama_input:
            df = pd.read_csv(file_csv, sep=None, engine='python')
            for col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').pipe(pd.to_numeric, errors='coerce')
            df = df.dropna()
            
            # LOGIKA TOLERANSI PER TITIK
            if 'Toleransi' in df.columns:
                df['Status'] = df.apply(lambda r: "OK ✅" if abs(r['Koreksi']) <= r['Toleransi'] else "NG ❌", axis=1)
            else:
                df['Status'] = df['Koreksi'].apply(lambda x: "OK ✅" if abs(x) <= toleransi_default else "NG ❌")
            
            # SIMPAN KE DATABASE (Menggunakan Nama Alat sebagai Key agar bisa simpan banyak)
            st.session_state.database_alat[nama_input] = {
                "sn": sn_input,
                "data": df,
                "final_status": "NG ❌" if any(df['Status'] == "NG ❌") else "OK ✅"
            }
            st.success(f"Data {nama_input} berhasil disimpan!")
            st.rerun()

    if st.session_state.database_alat:
        st.markdown("---")
        st.header("🗑️ Hapus Data")
        target_hapus = st.selectbox("Pilih Alat yang Dihapus:", list(st.session_state.database_alat.keys()))
        if st.button("Konfirmasi Hapus"):
            del st.session_state.database_alat[target_hapus]
            st.rerun()

# --- 6. TAMPILAN DATA (MULTIPLE CARDS) ---
if st.session_state.database_alat:
    st.write("### 📊 Ringkasan Status")
    # Menampilkan semua alat yang sudah disimpan dalam bentuk kolom
    cols = st.columns(len(st.session_state.database_alat))
    for i, (nama, info) in enumerate(st.session_state.database_alat.items()):
        cols[i].metric(label=f"{nama} ({info['sn']})", value=info['final_status'])
    
    st.markdown("---")
    # Menu pilih detail hanya berdasarkan Nama Alat
    selected_nama = st.selectbox("Pilih Alat untuk Lihat Detail:", list(st.session_state.database_alat.keys()))
    
    if selected_nama:
        res = st.session_state.database_alat[selected_nama]
        st.write(f"### Detail Sertifikat: {selected_nama} ({res['sn']})")
        st.table(res['data']) # Sekarang tabel akan muncul OK ✅ semua jika koreksi < toleransi tiap titik
else:
    st.info("Database Kosong. Silakan tambah data di sidebar.")
