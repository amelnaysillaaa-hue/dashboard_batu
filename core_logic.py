import os
import pandas as pd
import shutil
import json
from dotenv import load_dotenv
from google import genai
import requests
import streamlit as st

load_dotenv()

BASE_DIR = "data_survei"

def inisialisasi_sistem():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

def ambil_daftar_survei():
    if not os.path.exists(BASE_DIR):
        return []
    return sorted([d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))])

def tambah_survei_baru(nama):
    nama_bersih = nama.strip().lower()
    path = os.path.join(BASE_DIR, nama_bersih)
    if not os.path.exists(path):
        os.makedirs(path)
        return True, f"Survei '{nama.upper()}' berhasil dibuat."
    return False, f"Gagal! Survei '{nama.upper()}' sudah ada."

def hapus_survei(nama):
    path = os.path.join(BASE_DIR, nama)
    if os.path.exists(path):
        shutil.rmtree(path)
        return True, f"Survei '{nama.upper()}' telah dihapus selamanya."
    return False, "Gagal menghapus! Folder tidak ditemukan."

def simpan_data_upload(nama_survei, file, tahun):
    try:
        path = os.path.join(BASE_DIR, nama_survei, f"{tahun}.parquet")
        if file.name.endswith('.sav'):
            df = pd.read_spss(file)
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return False, "Format file tidak didukung."
        df.to_parquet(path, index=False)
        return True, f"Data {nama_survei.upper()} tahun {tahun} berhasil diunggah."
    except Exception as e:
        return False, f"Terjadi kesalahan: {str(e)}"

def ambil_info_data(nama_survei, tahun):
    path = os.path.join(BASE_DIR, nama_survei, f"{tahun}.parquet")
    if os.path.exists(path):
        return pd.read_parquet(path)
    return None

def simpan_perubahan_data(nama_survei, tahun, df_baru):
    try:
        path = os.path.join(BASE_DIR, nama_survei, f"{tahun}.parquet")
        df_baru.to_parquet(path, index=False)
        return True, f"Data {nama_survei.upper()} {tahun} berhasil diperbarui."
    except Exception as e:
        return False, f"Gagal menyimpan: {str(e)}"

def hapus_dataset_tahun(nama_survei, tahun):
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
    path = os.path.join(BASE_DIR, nama_survei, "viz_config.json")
    with open(path, 'w') as f:
        json.dump(config, f)

def ambil_viz_config(nama_survei):
    path = os.path.join(BASE_DIR, nama_survei, "viz_config.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

# ========== FUNGSI TAMBAHAN UNTUK INPUT MANUAL ==========
def tambah_data_manual(nama_survei, tahun, kategori, nilai):
    folder = os.path.join(BASE_DIR, nama_survei)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"{tahun}.parquet")
    df_baru = pd.DataFrame([{"Kategori": str(kategori), "Nilai": float(nilai)}])
    if os.path.exists(file_path):
        df_lama = pd.read_parquet(file_path)
        df_gabung = pd.concat([df_lama, df_baru], ignore_index=True)
        df_gabung.to_parquet(file_path, index=False)
    else:
        df_baru.to_parquet(file_path, index=False)
    return True, f"Berhasil menambah data: {kategori} = {nilai} (tahun {tahun})"

def hapus_semua_data_tahun(nama_survei, tahun):
    folder = os.path.join(BASE_DIR, nama_survei)
    file_path = os.path.join(folder, f"{tahun}.parquet")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True, f"Data tahun {tahun} berhasil dihapus."
    return False, f"Tidak ada data untuk tahun {tahun}."

# ========== FUNGSI GEMINI (DIPERBAIKI) ==========
def minta_interpretasi_gemini(ringkasan_data, nama_survei):
    # Ambil API Key dari Streamlit secrets
    api_key = st.secrets["OPENROUTER_API_KEY"]
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "openrouter/free",   # model gratis
        "messages": [
            {
                "role": "user",
                "content": f"Analisis singkat (3 kalimat) data {nama_survei}: {ringkasan_data}"
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Gagal memanggil AI: {str(e)}"