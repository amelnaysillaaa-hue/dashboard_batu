import os
import pandas as pd
import shutil
import json

BASE_DIR = "data_survei"

def inisialisasi_sistem():
    """Memastikan folder utama tersedia."""
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

def ambil_daftar_survei():
    """Mengambil semua folder survei yang ada."""
    if not os.path.exists(BASE_DIR):
        return []
    return sorted([d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))])

def tambah_survei_baru(nama):
    """Logika pembuatan folder survei."""
    nama_bersih = nama.strip().lower()
    path = os.path.join(BASE_DIR, nama_bersih)
    if not os.path.exists(path):
        os.makedirs(path)
        return True, f"Survei '{nama.upper()}' berhasil dibuat."
    return False, f"Gagal! Survei '{nama.upper()}' sudah ada."

def hapus_survei(nama):
    """Logika penghapusan folder survei."""
    path = os.path.join(BASE_DIR, nama)
    if os.path.exists(path):
        shutil.rmtree(path)
        return True, f"Survei '{nama.upper()}' telah dihapus selamanya."
    return False, "Gagal menghapus! Folder tidak ditemukan."

def simpan_data_upload(nama_survei, file, tahun):
    """Logika membaca dan menyimpan data ke format Parquet."""
    try:
        path = os.path.join(BASE_DIR, nama_survei, f"{tahun}.parquet")
        
        # 1. Membaca file
        if file.name.endswith('.sav'):
            df = pd.read_spss(file)
            df.attrs = {} 
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return False, "Format file tidak didukung."
        
        # 2. Simpan ke Parquet
        df.to_parquet(path, index=False)
        return True, f"Data {nama_survei.upper()} tahun {tahun} berhasil diunggah."
        
    except Exception as e:
        return False, f"Terjadi kesalahan: {str(e)}"
    
def ambil_info_data(nama_survei, tahun):
    """Membaca data untuk diinspeksi di halaman Detail."""
    path = os.path.join(BASE_DIR, nama_survei, f"{tahun}.parquet")
    if os.path.exists(path):
        return pd.read_parquet(path)
    return None

def simpan_perubahan_data(nama_survei, tahun, df_baru):
    """Menyimpan data hasil edit (timpa file lama tanpa backup)."""
    try:
        path = os.path.join(BASE_DIR, nama_survei, f"{tahun}.parquet")
        df_baru.to_parquet(path, index=False)
        return True, f"Data {nama_survei.upper()} {tahun} berhasil diperbarui."
    except Exception as e:
        return False, f"Gagal menyimpan: {str(e)}"
    
def hapus_dataset_tahun(nama_survei, tahun):
    """Menghapus satu file parquet tahun tertentu secara permanen."""
    try:
        path = os.path.join(BASE_DIR, nama_survei, f"{tahun}.parquet")
        if os.path.exists(path):
            os.remove(path)
            return True, f"Dataset {nama_survei.upper()} {tahun} berhasil dihapus."
        return False, "File tidak ditemukan."
    except Exception as e:
        return False, f"Gagal menghapus: {str(e)}"

def simpan_metadata_tahunan(nama_survei, tahun, kamus_data):
    path = os.path.join(BASE_DIR, nama_survei, f"{tahun}_metadata.json")
    with open(path, 'w') as f:
        json.dump(kamus_data, f)

def ambil_metadata_tahunan(nama_survei, tahun):
    path = os.path.join(BASE_DIR, nama_survei, f"{tahun}_metadata.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def simpan_viz_config(nama_survei, config):
    """Menyimpan konfigurasi filter dan daftar grafik ke JSON."""
    path = os.path.join(BASE_DIR, nama_survei, "viz_config.json")
    with open(path, 'w') as f:
        json.dump(config, f)

def ambil_viz_config(nama_survei):
    """Mengambil konfigurasi visualisasi jika ada."""
    path = os.path.join(BASE_DIR, nama_survei, "viz_config.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

import os
from dotenv import load_dotenv  
from google import genai 

load_dotenv() # Sekarang baris ini tidak akan error lagi

import os
from google import genai

def minta_interpretasi_gemini(nama_survei, ringkasan_data):
    api_key_saya = "AIzaSyA5egpXc1oJUx-SDYwIrx9Bs-HNWduuNpU" 
    
    client = genai.Client(api_key="AIzaSyA5egpXc1oJUx-SDYwIrx9Bs-HNWduuNpU")

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=f"Berikan analisis super singkat (maksimal 3 kalimat) untuk data {nama_survei}. "
                     f"Langsung ke poin utamanya saja, jangan pakai pembukaan basa-basi. "
                     f"Data: {ringkasan_data}"
            )
        return response.text
    except Exception as e:
        return f"Gagal panggil AI: {str(e)}"