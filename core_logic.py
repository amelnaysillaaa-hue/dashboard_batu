import os
import pandas as pd
import shutil
import json
import tempfile
import re
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = "data_survei"

# ==================== INISIALISASI & MANAJEMEN SURVEI ====================
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

# ==================== UPLOAD DATA (MANUAL & OTOMATIS) ====================
def simpan_data_upload(nama_survei, file, tahun):
    """Upload data dengan menentukan tahun manual (legacy)."""
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

def simpan_data_upload_auto(nama_survei, file_upload):
    """
    Upload file dan otomatis deteksi kolom kategori, nilai, dan tahun.
    Mendukung file dengan banyak kolom.
    """
    ext = file_upload.name.split('.')[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(file_upload.getvalue())
        tmp_path = tmp.name

    try:
        if ext == 'csv':
            df = pd.read_csv(tmp_path)
        elif ext == 'xlsx':
            df = pd.read_excel(tmp_path)
        elif ext == 'sav':
            import pyreadstat
            df, _ = pyreadstat.read_sav(tmp_path)
        else:
            return False, "Format file tidak didukung"
    except Exception as e:
        return False, f"Gagal membaca file: {e}"
    finally:
        os.unlink(tmp_path)

    # Helper functions
    def is_categorical(col):
        return df[col].dtype in ['object', 'category'] or str(df[col].dtype) == 'category'

    def is_numeric(col):
        return pd.api.types.is_numeric_dtype(df[col])

    def is_year_column(col):
        col_name = str(col)
        if re.search(r'tahun|year|thn', col_name, re.IGNORECASE):
            return True
        if is_numeric(col):
            uniq = df[col].dropna().unique()
            if len(uniq) <= 20:
                try:
                    if all(1900 <= float(x) <= 2100 for x in uniq):
                        return True
                except:
                    pass
        return False

    # 1. Deteksi kolom tahun
    tahun_col = None
    for col in df.columns:
        if is_year_column(col):
            tahun_col = col
            break

    # 2. Deteksi kolom kategori
    kategori_col = None
    for col in df.columns:
        if col == tahun_col:
            continue
        if is_categorical(col):
            if df[col].nunique() <= 50:
                kategori_col = col
                break
    if kategori_col is None:
        for col in df.columns:
            if col != tahun_col and not is_numeric(col):
                kategori_col = col
                break
    if kategori_col is None:
        kategori_col = df.columns[0]

    # 3. Deteksi kolom nilai
    nilai_col = None
    for col in df.columns:
        if col not in [tahun_col, kategori_col] and is_numeric(col):
            nilai_col = col
            break
    if nilai_col is None:
        for col in df.columns:
            if is_numeric(col) and col != tahun_col:
                nilai_col = col
                break
    if nilai_col is None:
        return False, "Tidak ditemukan kolom numerik untuk nilai."

    folder = os.path.join(BASE_DIR, nama_survei)
    os.makedirs(folder, exist_ok=True)

    if tahun_col is not None:
        # Format panjang
        df[tahun_col] = df[tahun_col].astype(str)
        tahun_unik = df[tahun_col].unique()
        for th in tahun_unik:
            df_th = df[df[tahun_col] == th][[kategori_col, nilai_col]].copy()
            df_th.columns = ['Kategori', 'Nilai']
            df_th = df_th.dropna(subset=['Nilai'])
            path_file = os.path.join(folder, f"{th}.parquet")
            df_th.to_parquet(path_file, index=False)
        return True, f"✅ Berhasil! {len(tahun_unik)} tahun data tersimpan. (Kategori='{kategori_col}', Nilai='{nilai_col}', Tahun='{tahun_col}')"
    else:
        # Coba format lebar (kolom lain sebagai tahun)
        year_candidates = []
        for col in df.columns:
            if col not in [kategori_col, nilai_col]:
                try:
                    yr = int(col)
                    if 2000 <= yr <= 2030:
                        year_candidates.append((col, yr))
                except:
                    pass
        if year_candidates:
            for col, yr in year_candidates:
                df_th = df[[kategori_col, col]].copy()
                df_th.columns = ['Kategori', 'Nilai']
                df_th = df_th.dropna(subset=['Nilai'])
                path_file = os.path.join(folder, f"{yr}.parquet")
                df_th.to_parquet(path_file, index=False)
            return True, f"✅ Berhasil! {len(year_candidates)} tahun data tersimpan (format lebar)."
        else:
            # Tidak ada petunjuk tahun, simpan sebagai tahun 2024
            df_th = df[[kategori_col, nilai_col]].copy()
            df_th.columns = ['Kategori', 'Nilai']
            df_th = df_th.dropna(subset=['Nilai'])
            path_file = os.path.join(folder, "2024.parquet")
            df_th.to_parquet(path_file, index=False)
            return True, "⚠️ Tidak ditemukan kolom tahun. Data disimpan sebagai tahun 2024. Anda dapat mengedit tahun di tabel data nanti."

# ==================== FUNGSI BACA DATA ====================
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

# ==================== METADATA ====================
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

# ==================== KONFIGURASI VISUALISASI ====================
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

# ==================== MANAJEMEN DATA MANUAL (EDITOR) ====================
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

def edit_data_manual(nama_survei, tahun, df_baru):
    folder = os.path.join(BASE_DIR, nama_survei)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"{tahun}.parquet")
    df_baru.to_parquet(file_path, index=False)
    return True, f"Data tahun {tahun} berhasil diperbarui."

def ambil_semua_data(nama_survei):
    folder = os.path.join(BASE_DIR, nama_survei)
    if not os.path.exists(folder):
        return pd.DataFrame(columns=["Tahun", "Kategori", "Nilai"])
    all_dfs = []
    for fname in os.listdir(folder):
        if fname.endswith(".parquet") and not fname.endswith("_metadata.json"):
            tahun = fname.replace(".parquet", "")
            df = pd.read_parquet(os.path.join(folder, fname))
            if "Kategori" not in df.columns or "Nilai" not in df.columns:
                if len(df.columns) == 2:
                    df.columns = ["Kategori", "Nilai"]
                else:
                    continue
            df = df[["Kategori", "Nilai"]].copy()
            df["Tahun"] = str(tahun)
            all_dfs.append(df)
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)[["Tahun", "Kategori", "Nilai"]]
    return pd.DataFrame(columns=["Tahun", "Kategori", "Nilai"])

# ==================== FUNGSI GEMINI VIA OPENROUTER ====================
def minta_interpretasi_gemini(ringkasan_data, nama_survei):
    api_key = st.secrets["OPENROUTER_API_KEY"]
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "openrouter/free",
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