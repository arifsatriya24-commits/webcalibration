import pandas as pd

file_spreadsheet = "data_kalibrasi.csv"
toleransi = 0.5

print("--- SISTEM VERIFIKASI POKA-YOKE DIGITAL ---")

try:
    # Poka-Yoke: Membaca CSV dengan deteksi pemisah otomatis (koma atau titik koma)
    df = pd.read_csv(file_spreadsheet, sep=None, engine='python')
    
    # Ambil data berdasarkan urutan kolom (Posisi 0 dan 1) 
    # Jadi tidak peduli namanya 'Nominal' atau 'Titik Ukur'
    nom_data = df.iloc[:, 0] 
    act_data = df.iloc[:, 1]
    
    print(f"Berhasil membaca {len(df)} titik ukur.")

    # Hitung Koreksi & Tentukan Status
    hasil_list = []
    for i in range(len(df)):
        nom = float(str(nom_data[i]).replace(',', '.'))
        act = float(str(act_data[i]).replace(',', '.'))
        kor = act - nom
        status = "OK ✅" if abs(kor) <= toleransi else "NG ❌"
        hasil_list.append([nom, act, kor, status])
    
    # Tampilkan Hasil
    print("\n" + "="*45)
    print(f"{'Nominal':<10} | {'Actual':<10} | {'Koreksi':<10} | {'Status'}")
    print("-" * 45)
    for h in hasil_list:
        print(f"{h[0]:<10} | {h[1]:<10} | {h[2]:<10.4f} | {h[3]}")
    print("="*45)

except Exception as e:
    print(f"\nOops, Robot bingung: {e}")
    print("Pastikan file CSV sudah di-save dan berisi angka.")

input("\nTekan Enter untuk keluar...")