import streamlit as st
import pandas as pd
import json
import os
import base64

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Develop Arif - Calibration", layout="wide")

# 2. WATERMARK (Diletakkan di sini agar selalu muncul di semua halaman)
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        right: 20px;
        bottom: 10px;
        color: grey;
        font-size: 14px;
        font-style: italic;
        z-index: 100;
    }
    </style>
    <div class="footer">
        Developed by Arif Satriya
    </div>
    """,
    unsafe_allow_html=True
)

# --- FUNGSI DATABASE ---
DB_FILE = "database_kalibrasi.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            for sn in data:
                data[sn]['data'] = pd.DataFrame(data[sn]['data'])
            return data
    return {}

def save_data(data):
    data_to_save = {}
    for sn, info in data.items():
        data_to_save[sn] = {
            "nama": info['nama'],
            "final_status": info['final_status'],
            "data": info['data'].to_dict(orient='records')
        }
    with open(DB_FILE, "w") as f:
        json.dump(data_to_save, f)

if 'database_alat' not in st.session_state:
    st.session_state.database_alat = load_data()

# --- 3. SISTEM LOGIN ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def login():
    nama_file_logo = "logo.png" 
    if os.path.exists(nama_file_logo):
        with open(nama_file_logo, "rb") as f:
            data = f.read()
            encoded = base64.b64encode(data).decode()
        logo_html = f"<div style='text-align: center;'><img src='data:image/png;base64,{encoded}' width='180'><h1>Portal Calibration Security</h1></div>"
    else:
        logo_html = "<h1 style='text-align: center;'>🔐 Portal Calibration Security</h1>"

    st.markdown(logo_html, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Masuk ke Dashboard"):
            if user == "arif" and password == "000":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Username atau Password Salah!")
    st.stop()

if not st.session_state.authenticated:
    login()

# --- 4. DASHBOARD UTAMA ---
st.title("🛡️ Hasil Evaluasi Kalibrasi")
st.markdown("---")

with st.sidebar:
    if st.button("🚪 Keluar Sistem"):
        st.session_state.authenticated = False
        st.rerun()
    
    st.markdown("---")
    st.header("➕ Tambah Evaluasi Alat")
    nama_alat = st.text_input("Nama Alat")
    no_seri = st.text_input("Nomor Seri")
    satuan = st.selectbox("Satuan Alat", ["mm", "rpm", "kg", "celcius"])
    toleransi = st.number_input(f"Batas Toleransi ({satuan})", value=0.5 if satuan == "mm" else 10.0)
    
    file_csv = st.file_uploader("Upload Data CSV", type="csv")
    
    if st.button("Simpan Hasil Evaluasi"):
        if file_csv and no_seri:
            df_temp = pd.read_csv(file_csv, sep=None, engine='python')
            for col in df_temp.columns:
                df_temp[col] = df_temp[col].astype(str).str.replace('"', '').str.replace(',', '.')
                df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce')
            df_temp = df_temp.dropna().reset_index(drop=True)
            
            if 'Toleransi' in df_temp.columns:
                df_temp['Status'] = df_temp.apply(lambda r: "OK ✅" if abs(r['Koreksi']) <= r['Toleransi'] else "NG ❌", axis=1)
                info_tol = "Berdasarkan Kolom CSV"
            else:
                df_temp['Status'] = df_temp['Koreksi'].apply(lambda x: "OK ✅" if abs(x) <= toleransi else "NG ❌")
                info_tol = f"{toleransi} {satuan}"
            
            st.session_state.database_alat[no_seri] = {
                "nama": nama_alat, "data": df_temp, "satuan": satuan, "info_toleransi": info_tol,
                "final_status": "NG ❌" if any(df_temp['Status'] == "NG ❌") else "OK ✅"
            }
            save_data(st.session_state.database_alat)
            st.success(f"Data {nama_alat} Tersimpan!")
            st.rerun()

    if st.session_state.database_alat:
        st.markdown("---")
        st.header("🗑️ Hapus Data")
        list_hapus_label = {f"{info['nama']} ({sn})": sn for sn, info in st.session_state.database_alat.items()}
        alat_mau_dihapus_label = st.selectbox("Pilih Alat untuk Dihapus:", list(list_hapus_label.keys()))
        if st.button("Konfirmasi Hapus"):
            sn_target = list_hapus_label[alat_mau_dihapus_label]
            del st.session_state.database_alat[sn_target]
            save_data(st.session_state.database_alat)
            st.rerun()

if st.session_state.database_alat:
    st.write("### 📊 Status Alat Saat Ini")
    jml_alat = len(st.session_state.database_alat)
    cols = st.columns(max(jml_alat, 1))
    for i, (sn, info) in enumerate(st.session_state.database_alat.items()):
        with cols[i]:
            st.metric(label=f"{info['nama']} ({sn})", value=info['final_status'])

    st.markdown("---")
    pilihan_label = {f"{info['nama']} - {sn}": sn for sn, info in st.session_state.database_alat.items()}
    selected_label = st.selectbox("Pilih Alat untuk Lihat Detail:", list(pilihan_label.keys()))
    pilihan_sn = pilihan_label[selected_label]
    if pilihan_sn:
        res = st.session_state.database_alat[pilihan_sn]
        st.write(f"#### Detail Sertifikat: {res['nama']} - {pilihan_sn}")
        st.table(res['data'])
else:
    st.info("Database Kosong.")