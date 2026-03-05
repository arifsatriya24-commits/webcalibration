import streamlit as st
import pandas as pd
import json
import os
import base64
from streamlit_gsheets import GSheetsConnection

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Develop Arif - Calibration", layout="wide")

# 2. WATERMARK
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

# --- 3. FUNGSI DATABASE (GOOGLE SHEETS VERSION) ---
# Menghubungkan ke Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Membaca data dari Google Sheets (ttl=0 agar data selalu paling baru)
        df = conn.read(ttl="0s")
        if df.empty:
            return {}
        
        # Mengubah data dari tabel Google Sheets kembali ke format Dictionary (Session State)
        data_dict = {}
        for _, row in df.iterrows():
            data_dict[str(row['no_seri'])] = {
                "nama": row['nama'],
                "satuan": row['satuan'],
                "info_toleransi": row['info_toleransi'],
                "final_status": row['final_status'],
                "data": pd.DataFrame(json.loads(row['data_json'])) # Tabel CSV disimpan sebagai JSON
            }
        return data_dict
    except:
        return {}

def save_to_sheets(all_data):
    # Mengubah format Dictionary ke Tabel (DataFrame) untuk diupload ke Google Sheets
    rows = []
    for sn, info in all_data.items():
        rows.append({
            "no_seri": sn,
            "nama": info['nama'],
            "satuan": info['satuan'],
            "info_toleransi": info['info_toleransi'],
            "final_status": info['final_status'],
            "data_json": json.dumps(info['data'].to_dict(orient='records'))
        })
    
    if rows:
        updated_df = pd.DataFrame(rows)
        conn.update(data=updated_df)

# Inisialisasi Database
if 'database_alat' not in st.session_state:
    st.session_state.database_alat = load_data()

# --- 4. SISTEM LOGIN ---
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

# --- 5. DASHBOARD UTAMA ---
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
            
            # Simpan ke Session State
            st.session_state.database_alat[no_seri] = {
                "nama": nama_alat, "data": df_temp, "satuan": satuan, "info_toleransi": info_tol,
                "final_status": "NG ❌" if any(df_temp['Status'] == "NG ❌") else "OK ✅"
            }
            
            # SIMPAN PERMANEN KE GOOGLE SHEETS
            save_to_sheets(st.session_state.database_alat)
            
            st.success(f"Data {nama_alat} Berhasil Tersimpan di Cloud!")
            st.rerun()

    if st.session_state.database_alat:
        st.markdown("---")
        st.header("🗑️ Hapus Data")
        list_hapus_label = {f"{info['nama']} ({sn})": sn for sn, info in st.session_state.database_alat.items()}
        alat_mau_dihapus_label = st.selectbox("Pilih Alat untuk Dihapus:", list(list_hapus_label.keys()))
        if st.button("Konfirmasi Hapus"):
            sn_target = list_hapus_label[alat_mau_dihapus_label]
            del st.session_state.database_alat[sn_target]
            # Update perubahan hapus ke Cloud
            save_to_sheets(st.session_state.database_alat)
            st.rerun()

# Menampilkan Ringkasan
if st.session_state.database_alat:
    st.write("### 📊 Status Alat Saat Ini")
    jml_alat = len(st.session_state.database_alat)
    # Membuat kolom maksimal 4 agar tidak terlalu rapat
    n_cols = min(jml_alat, 4)
    cols = st.columns(n_cols)
    
    for i, (sn, info) in enumerate(st.session_state.database_alat.items()):
        with cols[i % 4]:
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