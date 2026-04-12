import streamlit as st
import core_logic as core
import pandas as pd
import plotly.express as px
import os
import textwrap
import shutil 

# --- LOGIKA GPS (QUERY PARAMS) & NAVIGASI ---
def inisialisasi_state():
    """Memastikan semua variabel memori tersedia saat aplikasi dijalankan."""
    params = st.query_params   
    if 'halaman' not in st.session_state:
        st.session_state.halaman = params.get("p", "Landing")   
    if 'survei_aktif' not in st.session_state:
        st.session_state.survei_aktif = params.get("s", None)
    if 'target_edit_metadata' not in st.session_state:
        st.session_state.target_edit_metadata = params.get("t", None)
    if 'dialog_aktif' not in st.session_state: st.session_state.dialog_aktif = None
    if 'sukses_proses' not in st.session_state: st.session_state.sukses_proses = False

def pindah_halaman(nama_halaman, survei=None, target_edit=None):
    """Fungsi navigasi yang membersihkan URL secara otomatis."""
    st.session_state.halaman = nama_halaman
    st.session_state.survei_aktif = survei
    st.session_state.target_edit_metadata = target_edit
   
    new_params = {"p": nama_halaman}
    if survei: new_params["s"] = survei
    if target_edit: new_params["t"] = target_edit
   
    st.query_params.clear()
    for k, v in new_params.items():
        st.query_params[k] = v
   
    st.rerun() # <--- PINDAH KE SINI (Harus di dalam fungsi pindah_halaman)

def wrap_judul(text, width=30):
    if not text: return ""
    # Memotong teks setiap 40 karakter dan menyisipkan <br> (HTML baris baru)
    return "<br>".join(textwrap.wrap(text, width=width))

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Lexend:wght@400;700&family=Montserrat:wght@400;700&family=Poppins:wght@400;700&family=Roboto:wght@400;700&family=Open+Sans:wght@400;700&display=swap" rel="stylesheet">
   
    <style>
    /* 1. Ngecilin teks umum di seluruh dashboard */
    html, body, [class*="css"] {
        font-size: 14px;
    }
   
    /* 2. Khusus untuk teks di Sidebar agar lebih compact */
    [data-testid="stSidebar"] {
        font-size: 13px;
    }

    /* 3. Opsional: Ngecilin font di dalam tombol (st.button) */
    .stButton>button {
        font-size: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 1. INISIALISASI
st.set_page_config(page_title="Dashboard Statistik Batu", layout="wide")
core.inisialisasi_sistem()
inisialisasi_state()

if 'halaman' not in st.session_state:
    st.session_state.halaman = "Landing"
if 'survei_aktif' not in st.session_state:
    st.session_state.survei_aktif = None
if 'dialog_aktif' not in st.session_state:
    st.session_state.dialog_aktif = None
if 'sukses_proses' not in st.session_state:
    st.session_state.sukses_proses = False

# --- BAGIAN POP-UP (DIALOG) ---
@st.dialog("Tambah Survei Baru")
def pop_tambah_survei():
    if st.session_state.sukses_proses:
        st.success("✅ Berhasil! Wadah survei baru telah dibuat.")
        if st.button("Selesai & Tutup", width='stretch'):
            st.session_state.sukses_proses = False
            st.session_state.dialog_aktif = None
            pindah_halaman("Landing")
    else:
        nama = st.text_input("Nama Survei:", placeholder="Contoh: Susenas")
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("Simpan", type="primary", width='stretch'):
            if nama:
                sukses, pesan = core.tambah_survei_baru(nama)
                if sukses:
                    st.session_state.sukses_proses = True
                    st.rerun()
                else:
                    st.error(pesan)
            else:
                st.warning("Nama harus diisi!")
        if c2.button("Batal", width='stretch'):
            st.session_state.dialog_aktif = None
            st.rerun()

@st.dialog("Konfirmasi Hapus")
def pop_hapus_survei():
    nama = st.session_state.target_hapus
    if st.session_state.sukses_proses:
        st.success(f"🗑️ Survei {nama.upper()} berhasil dihapus.")
        if st.button("Tutup", width='stretch'):
            st.session_state.sukses_proses = False
            st.session_state.dialog_aktif = None
            st.session_state.halaman = "Landing"
            st.rerun()
    else:
        st.warning(f"Apakah Anda yakin ingin menghapus **{nama.upper()}**?")
        st.write("Tindakan ini akan menghapus seluruh data di dalamnya secara permanen.")
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("Ya, Hapus", type="primary", width='stretch'):
            sukses, pesan = core.hapus_survei(nama)
            if sukses:
                st.session_state.sukses_proses = True
                st.rerun()
        if c2.button("Batal", width='stretch'):
            st.session_state.dialog_aktif = None
            st.rerun()

@st.dialog("Status Unggah Data")
def pop_status_upload():
    sukses = st.session_state.upload_sukses
    pesan = st.session_state.upload_pesan
    if sukses:
        st.success("🚀 Berhasil Mengunggah!")
        st.write(pesan)
        st.balloons()
    else:
        st.error("❌ Gagal Mengunggah")
        st.write(pesan)
   
    if st.button("Tutup", width='stretch'):
        st.session_state.dialog_aktif = None
        st.rerun()

@st.dialog("Konfirmasi Edit Kolom")
def pop_konfirmasi_edit():
    cols_to_drop = st.session_state.kolom_target_hapus
    st.warning(f"Anda akan menghapus **{len(cols_to_drop)}** kolom secara permanen.")
    st.write(f"Kolom: {', '.join(cols_to_drop)}")
    st.write("---")
   
    if st.session_state.sukses_proses:
        st.success("✅ Kolom berhasil dihapus!")
        if st.button("Tutup", width='stretch'):
            st.session_state.sukses_proses = False
            st.session_state.dialog_aktif = None
            st.rerun()
    else:
        c1, c2 = st.columns(2)
        if c1.button("Ya, Hapus Kolom", type="primary", width='stretch'):
            df_asli = core.ambil_info_data(st.session_state.edit_survei, st.session_state.edit_tahun)
            df_baru = df_asli.drop(columns=cols_to_drop)
            sukses, pesan = core.simpan_perubahan_data(st.session_state.edit_survei, st.session_state.edit_tahun, df_baru)
            if sukses:
                st.session_state.sukses_proses = True
                st.rerun()
            else:
                st.error(pesan)
        if c2.button("Batal", width='stretch'):
            st.session_state.dialog_aktif = None
            st.rerun()

@st.dialog("Konfirmasi Hapus Dataset")
def pop_hapus_dataset_tahun():
    nama = st.session_state.edit_survei
    tahun = st.session_state.edit_tahun
   
    if st.session_state.sukses_proses:
        st.success(f"🗑️ Dataset {nama.upper()} {tahun} berhasil dihapus.")
        if st.button("Tutup", width='stretch'):
            st.session_state.sukses_proses = False
            st.session_state.dialog_aktif = None
            st.rerun()
    else:
        st.warning(f"Apakah Anda yakin ingin menghapus SELURUH data **{nama.upper()}** tahun **{tahun}**?")
        st.write("Tindakan ini tidak dapat dibatalkan.")
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("Ya, Hapus Dataset", type="primary", width='stretch'):
            sukses, pesan = core.hapus_dataset_tahun(nama, tahun)
            if sukses:
                st.session_state.sukses_proses = True
                st.rerun()
            else:
                st.error(pesan)
        if c2.button("Batal", width='stretch'):
            st.session_state.dialog_aktif = None
            st.rerun()

@st.dialog("Konfirmasi Salin Kamus")
def pop_salin_metadata():
    sumber = st.session_state.salin_sumber
    target = st.session_state.salin_target
    survei = st.session_state.target_edit_metadata
   
    if st.session_state.sukses_proses:
        st.success(f"✅ Berhasil menyalin kamus dari {sumber} ke {target}!")
        if st.button("Lihat Perubahan", width='stretch'):
            kamus_baru = core.ambil_metadata_tahunan(survei, target)
           
            for col, info in kamus_baru.items():
                st.session_state[f"al_{target}_{col}"] = info.get("alias", col)
                st.session_state[f"sh_{target}_{col}"] = info.get("show", True)
           
            st.session_state.sukses_proses = False
            st.session_state.dialog_aktif = None
            st.rerun()
    else:
        st.warning(f"Salin kamus dari tahun **{sumber}** ke **{target}**?")
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("Ya, Terapkan", type="primary", width='stretch'):
            kamus_copy = core.ambil_metadata_tahunan(survei, sumber)
            core.simpan_metadata_tahunan(survei, target, kamus_copy)
            st.session_state.sukses_proses = True
            st.rerun()
        if c2.button("Batal", width='stretch'):
            st.session_state.dialog_aktif = None
            st.rerun()

# --- PEMICU DIALOG (Trigger) ---
if st.session_state.dialog_aktif == "tambah": pop_tambah_survei()
elif st.session_state.dialog_aktif == "hapus": pop_hapus_survei()
elif st.session_state.dialog_aktif == "status_upload": pop_status_upload()
elif st.session_state.dialog_aktif == "konfirmasi_edit": pop_konfirmasi_edit()
elif st.session_state.dialog_aktif == "hapus_dataset": pop_hapus_dataset_tahun()
elif st.session_state.dialog_aktif == "salin_metadata": pop_salin_metadata()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("🗂️ Menu Utama")
if st.sidebar.button("🏠 Beranda", width='stretch'): # DIUBAH
    pindah_halaman("Landing")
if st.sidebar.button("💾 Detail & Edit Data", width='stretch'):
    pindah_halaman("Detail")
st.sidebar.divider()
daftar = core.ambil_daftar_survei()
st.sidebar.subheader("🔎 Pilih Survei")
selected = st.sidebar.selectbox(
    "Daftar:",
    daftar if daftar else ["Belum ada survei"],
    format_func=lambda x: x.upper()
)

if selected != "Belum ada survei":
    if st.sidebar.button(f"Buka {selected.upper()}", width='stretch'):
        pindah_halaman("Visualisasi", survei=selected)
st.sidebar.divider()

if st.sidebar.button("➕ Tambah Survei Baru", width='stretch'):
    st.session_state.dialog_aktif = "tambah"
    st.rerun()

if st.sidebar.button("⚙️ Kelola Survei", width='stretch'):
    pindah_halaman("Kelola")



# --- HALAMAN UTAMA ---
if st.session_state.halaman == "Landing":
    st.title("🏔️ Selamat Datang")
    st.header("Dashboard Visualisasi Data Statistik Kota Batu")
    st.markdown("Dashboard ini dirancang untuk mempermudah pembuatan grafik hasil survei secara otomatis.")
    st.info(f"Terdapat **{len(daftar)}** jenis survei yang tersimpan dalam sistem.")

elif st.session_state.halaman == "Visualisasi":
    snama = st.session_state.survei_aktif
    if not snama:
        st.warning("⚠️ Silakan pilih survei di sidebar.")
        st.stop()
        
    # --- 1. LOAD CONFIG ---
    if 'last_loaded' not in st.session_state or st.session_state.last_loaded != snama:
        config = core.ambil_viz_config(snama)
        st.session_state.viz_state = config if config else {"charts": []}
        st.session_state.last_loaded = snama

    st.title(f"📊 Dashboard Visualisasi: {snama.upper()}")

    # --- 2. HEADER: UNGGAH & SIMPAN ---
    path_s = os.path.join("data_survei", snama)
    if not os.path.exists(path_s): os.makedirs(path_s) # Pastikan folder ada
    years_avail = sorted([f.replace(".parquet", "") for f in os.listdir(path_s) if f.endswith(".parquet")])
   
    col_up, col_sv = st.columns([3, 1])
    with col_up.expander("⬆️ Unggah Data Baru"):
        f_up = st.file_uploader("Upload .csv, .sav, .xlsx", type=['csv', 'sav', 'xlsx'], key="viz_up")
        th_up = st.number_input("Tahun", 2020, 2030, 2026)
        if st.button("Konfirmasi Unggah", width='stretch'):
            if f_up:
                sukses, pesan = core.simpan_data_upload(snama, f_up, th_up)
                if sukses:
                    st.session_state.upload_sukses = sukses
                    st.session_state.upload_pesan = pesan
                    st.session_state.dialog_aktif = "status_upload"
                    st.rerun()
                else: st.error(pesan)
    with col_sv:
        if st.button("💾 Simpan Dashboard", width='stretch', type="primary"):
            core.simpan_viz_config(snama, st.session_state.viz_state)
            st.success("Tersimpan!")
    st.divider()

    # --- 3. RENDER GRAFIK ---
    charts = st.session_state.viz_state["charts"]
    for i in range(0, len(charts), 2):
        row_cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(charts):
                with row_cols[j]:
                    with st.container(border=True):
                        ch = charts[idx]
                        # PENTING: ID Unik berdasarkan INDEX untuk mencegah bentrok
                        id_unik = f"{snama}_viz_{idx}"
                        # --- JEMBATAN NARASI ---
                        if id_unik not in st.session_state:
                            # Ambil isi narasi dari file (ch) kalau di memori masih kosong
                            st.session_state[id_unik] = ch.get('interpretasi_saved', "")
                       
                        with st.expander(f"⚙️ Pengaturan Grafik {idx+1}", expanded=not ch.get('years')):
                            n_title = st.text_input("Judul Grafik", value=ch.get('title', f"Grafik {idx+1}"), key=f"title_{idx}")
                            saved_years = ch.get('years', [])
                            valid_default = [y for y in saved_years if y in years_avail]
                            sel_years = st.multiselect(f"Pilih Tahun Data:", years_avail, default=valid_default, key=f"yr_{idx}")
                                                        
                            n_font = ch.get('font_family', 'Arial')
                            n_size = ch.get('font_size', 12)
                            c_txt = ch.get('color_txt', '#000000')
                            c_bg = ch.get('color_bg', '#FFFFFF')
                            new_color_map = ch.get('color_map', {})
                           
                            all_cols_raw = []
                            current_meta = {}
                            if sel_years:
                                df_s = pd.read_parquet(os.path.join(path_s, f"{sel_years[0]}.parquet"))
                                all_cols_raw = df_s.columns.tolist()
                                current_meta = core.ambil_metadata_tahunan(snama, sel_years[0])

                            def format_label(col_raw):
                                if col_raw == "Pilih Tahun...": return col_raw
                                alias = current_meta.get(col_raw, {}).get('alias', '')
                                return f"{col_raw} ({alias})" if alias and alias != col_raw else col_raw
                           
                            cc1, cc2 = st.columns(2)
                            n_type = cc1.selectbox("Tipe", ["Bar", "Line", "Box"], index=["Bar", "Line", "Box"].index(ch.get('type', 'Bar')), key=f"t_{idx}")
                            n_x = cc2.selectbox("Sumbu X", all_cols_raw if all_cols_raw else ["Pilih Tahun..."], index=all_cols_raw.index(ch['x']) if ch['x'] in all_cols_raw else 0, format_func=format_label, key=f"x_{idx}")
                           
                            cc3, cc4 = st.columns(2)
                            list_agg = ["Jumlah (Count)", "Rata-rata (Mean)", "Total (Sum)", "Nilai Asli (Value)"]
                            n_agg = cc3.selectbox("Fungsi Y", list_agg, index=list_agg.index(ch.get('agg', 'Jumlah (Count)')), key=f"a_{idx}")
                           
                            n_y = None
                            if n_agg != "Jumlah (Count)":
                                y_def = ch.get('y', all_cols_raw[0] if all_cols_raw else None)
                                n_y = cc4.selectbox("Variabel Y", all_cols_raw, index=all_cols_raw.index(y_def) if y_def in all_cols_raw else 0, format_func=format_label, key=f"y_{idx}")

                            # --- STEP 1: PROSES DATA DULU ---
                            if sel_years:
                                # --- INI KUNCINYA: Kumpulkan data dari semua tahun ---
                                dfs_local = []
                                for y in sel_years:
                                    try:
                                        df_y = pd.read_parquet(os.path.join(path_s, f"{y}.parquet"))
                                        # Tambahkan kolom tahun supaya bisa di-melt nanti
                                        df_y['Tahun'] = str(y)
                                        dfs_local.append(df_y)
                                    except:
                                        continue
                               
                                # Pastikan data ada sebelum di-concat
                                if dfs_local:
                                    df_plot_induk = pd.concat(dfs_local, ignore_index=True)
                                   
                                    # Ambil kolom untuk metadata (pakai data pertama saja)
                                    all_cols_raw = df_plot_induk.columns.tolist()
                                    current_meta = core.ambil_metadata_tahunan(snama, sel_years[0])
                                   
                                    # --- PROSES MELT DISINI (Supaya batang jadi banyak) ---
                                    # Misal sumbu X adalah kolom pertama, sisanya jadi Kategori
                                    res_melt = df_plot_induk.melt(
                                        id_vars=[n_x if n_x in all_cols_raw else all_cols_raw[0], 'Tahun'],
                                        var_name="Kategori",
                                        value_name="Nilai"
                                    )

                               # --- SEMUA KODE DI BAWAH INI HARUS MASUK KE DALAM "IF SEL_YEARS" ---
                                st.write("---")
                                st.markdown("**🎨 Kustomisasi Tampilan**")

                                # 1. Pilih Font & Ukuran
                                list_font = ["Arial", "Courier New", "Verdana", "Times New Roman", "Comic Sans MS", "Lexend", "Hanken Grotesk", "Montserrat", "Poppins", "Roboto", "Open Sans"]
                                saved_font = ch.get('font_family', 'Arial')
                                saved_size = ch.get('font_size', 12) # Ambil size lama atau default 12

                                cc_f1, cc_f2 = st.columns([2, 1])
                                n_font = cc_f1.selectbox("Pilih Font", list_font, index=list_font.index(saved_font) if saved_font in list_font else 0, key=f"font_{idx}")
                                n_size = cc_f2.number_input("Ukuran", 8, 40, int(saved_size), key=f"size_{idx}") # Tambahan ukuran font

                                # 2. Warna Dasar (Teks & BG)
                                cc_txt, cc_bg = st.columns(2)
                                c_txt = cc_txt.color_picker("Warna Teks", ch.get('color_txt', '#000000'), key=f"cp_txt_{idx}")
                                c_bg = cc_bg.color_picker("Warna Background", ch.get('color_bg', '#FFFFFF'), key=f"cp_bg_{idx}")

                                # STEP 3: LOGIKA PENYIMPANAN
                                if (new_color_map != ch.get('color_map') or n_font != ch.get('font_family')):
                                    ch['color_map'] = new_color_map
                                    ch['font_family'] = n_font # Jangan lupa simpan font-nya juga!
                                    st.session_state.charts = charts
                                    st.rerun()

                            else:
                                # Tampilkan pesan kalau tahun belum dipilih
                                st.info("Silakan pilih tahun pada pengaturan di atas untuk menampilkan grafik.")
                               
                         # --- Tambahan Kontrol Interpretasi ---
                        st.markdown("**📝 Pengaturan Teks Interpretasi**")

                        # 1. Kotak Pembatas
                        use_border = st.checkbox("Pakai Kotak Pembatas", value=ch.get('ai_border', False), key=f"ai_brd_chk_{idx}")
                       
                        col_brd1, col_brd2, col_brd3 = st.columns(3)
                        c_brd_bg = col_brd1.color_picker("Warna Isi Kotak", ch.get('ai_bg_col', '#FFFFFF'), key=f"ai_bg_cp_{idx}", disabled=not use_border)
                        c_brd_line = col_brd2.color_picker("Warna Garis", ch.get('ai_line_col', '#000000'), key=f"ai_line_cp_{idx}", disabled=not use_border)
                        v_brd_width = col_brd3.number_input("Tebal Garis", 0, 5, ch.get('ai_line_w', 1), key=f"ai_line_w_{idx}", disabled=not use_border)


                        # 2. Pengaturan Posisi & Lebar
                        cc_ai1, cc_ai2 = st.columns(2)
                        v_jarak = cc_ai1.slider("Jarak Teks ke Grafik (Y)", -0.5, -0.05, float(ch.get('ai_y', -0.2)), key=f"ai_y_sld_{idx}")
                       
                        # Ambil index untuk selectbox rata teks
                        list_align = ["left", "center", "right"]
                        current_align = ch.get('ai_align', 'left')
                        idx_align = list_align.index(current_align) if current_align in list_align else 0
                        v_align = cc_ai2.selectbox("Rata Teks AI", list_align, index=idx_align, key=f"ai_align_sel_{idx}")

                        # 3. Slider Lebar
                        v_lebar = st.slider("Lebar Kotak Teks (Piksel)", 200, 1000, int(ch.get('ai_w', 500)), step=10, key=f"ai_w_sld_{idx}")

                       # --- LOGIKA PENYIMPANAN (UPDATE CH) ---
                        if (n_font != ch.get('font_family') or
                            n_size != ch.get('font_size') or
                            c_txt != ch.get('color_txt') or    # Pastikan warna teks juga masuk
                            c_bg != ch.get('color_bg') or      # Pastikan background juga masuk
                            use_border != ch.get('ai_border') or
                            v_jarak != ch.get('ai_y') or
                            v_align != ch.get('ai_align') or
                            v_lebar != ch.get('ai_w') or
                            new_color_map != ch.get('color_map')): # Warna diagram per tahun
                           
                            # SIMPAN NILAI BARU KE DICTIONARY 'ch'
                            ch['font_family'] = n_font
                            ch['font_size'] = n_size
                            ch['color_txt'] = c_txt
                            ch['color_bg'] = c_bg
                            ch['color_map'] = new_color_map
                           
                            # Simpan setting interpretasi
                            ch['ai_border'] = use_border
                            ch['ai_bg_col'] = c_brd_bg
                            ch['ai_line_col'] = c_brd_line
                            ch['ai_line_w'] = v_brd_width
                            ch['ai_y'] = v_jarak
                            ch['ai_align'] = v_align
                            ch['ai_w'] = v_lebar
                           
                            # PAKSA REFRESH
                            st.rerun()

                        # Tombol hapus
                        if st.button(f"🗑️ Hapus Grafik {idx+1}", key=f"del_{idx}", width='stretch'):
                            charts.pop(idx)
                            st.rerun()
                               
                        if sel_years:
                            try:
                                # --- 1. PROSES DATA ---
                                dfs_local = []
                                for y in sel_years:
                                    df_y = pd.read_parquet(os.path.join(path_s, f"{y}.parquet"))
                                    km = core.ambil_metadata_tahunan(snama, y)
                                    peta = {k: v.get('alias', k) for k, v in km.items()}
                                    df_y = df_y.rename(columns=peta)
                                    df_y['_Tahun_File_'] = y
                                    dfs_local.append(df_y)
                                    new_color_map = {}

                                df_plot = pd.concat(dfs_local, ignore_index=True)
                                x_f = peta.get(n_x, n_x)
                                y_f = peta.get(n_y, n_y) if n_y else None
                                df_plot[x_f] = df_plot[x_f].astype(str)

                                if y_f and n_agg != "Nilai Asli (Value)":
                                    df_plot[y_f] = pd.to_numeric(df_plot[y_f], errors='coerce')

                                df_clean = df_plot.dropna(subset=[y_f] if y_f else [])

                                # --- 2. AGREGASI ---
                                if "Count" in n_agg:
                                    res = df_clean.groupby(['_Tahun_File_', x_f]).size().reset_index(name='Nilai')
                                    label_y_desc = f"Frekuensi {x_f}"
                                elif "Sum" in n_agg:
                                    res = df_clean.groupby(['_Tahun_File_', x_f])[y_f].sum().reset_index(name='Nilai')
                                    label_y_desc = f"Total {y_f}"
                                elif "Mean" in n_agg:
                                    res = df_clean.groupby(['_Tahun_File_', x_f])[y_f].mean().reset_index(name='Nilai')
                                    label_y_desc = f"Rata-rata {y_f}"
                                else:
                                    res = df_clean[['_Tahun_File_', x_f, y_f]].copy().rename(columns={y_f: 'Nilai'})
                                    label_y_desc = y_f

                                res = res.sort_values(by=x_f)

                                # --- 3. PREPARASI TAMPILAN & STYLE ---
                                n_orientasi = ch.get('orientasi', "Vertical")
                                opt_posisi = st.session_state.get(f"pos_ai_{idx}", "Bawah")
                                isi_ai = st.session_state.get(id_unik, "")

                                n_font = st.session_state.get(f"font_{idx}", ch.get('font_family', 'Arial'))
                                size_pake = st.session_state.get(f"size_{idx}", ch.get('font_size', 12))
                                c_txt = st.session_state.get(f"cp_txt_{idx}", ch.get('color_txt', '#000000'))
                                c_bg = st.session_state.get(f"cp_bg_{idx}", ch.get('color_bg', '#FFFFFF'))

                                # Atur margin dan tinggi berdasarkan posisi AI
                                h_pake = 450
                                b_marg = 120 if (isi_ai and opt_posisi == "Dalam Grafik") else 80

                                # Reshape data untuk Plotly (Tahun sebagai Legend)
                                res_reset = res.reset_index(drop=True).copy()
                                kolom_bersih = [c for c in res_reset.columns if c not in ['_Tahun_File_']]
                                df_fix = res_reset[kolom_bersih].copy()
                                df_tab = df_fix.set_index(df_fix.columns[0]).T.reset_index()
                                df_tab.columns = ["Jenis Harga"] + list(df_tab.columns[1:])
                                res_melt = df_tab.melt(id_vars=["Jenis Harga"], var_name="Tahun", value_name="Nilai Ekonomi")


                                # -# --- 4. PEMBUATAN GRAFIK & KUSTOM WARNA ---
                                # 1. Rapikan Kolom secara Langsung (Pasti Aman)
                                # Dari hasil melt di atas, urutannya pasti: ["Jenis Harga", "Tahun", "Nilai Ekonomi"]
                                res_plot = res_melt.copy()
                                res_plot.columns = ['Kategori', 'Tahun', 'Nilai']
                                
                                # Paksa jadi string biar sinkron sama warna kustom
                                res_plot['Kategori'] = res_plot['Kategori'].astype(str)
                                res_plot['Tahun'] = res_plot['Tahun'].astype(str)

                                # 2. MUNCULKAN COLOR PICKER DI SINI
                                st.write("🎨 **Warna Tiap Kategori:**")
                                dict_warna = ch.get('color_map', {})
                                list_batang = res_plot['Kategori'].unique()
                                
                                new_color_map = {}
                                cols_warna = st.columns(min(len(list_batang), 4))
                                
                                for i, nama_batang in enumerate(list_batang):
                                    with cols_warna[i % 4]:
                                        label_batang = str(nama_batang)
                                        warna_def = dict_warna.get(label_batang, "#636EFA")
                                        warna_pilih = st.color_picker(f"{label_batang}", warna_def, key=f"cp_final_{idx}_{i}")
                                        new_color_map[label_batang] = warna_pilih
                                
                                # Simpan warna kalau ada perubahan
                                if new_color_map != dict_warna:
                                    ch['color_map'] = new_color_map

                                # 3. FITUR SWITCH ROW/COLUMN
                                mode_grafik = st.radio("🔄 Switch Tampilan:", 
                                                       ["Tahun di Sumbu X (Warna = Kategori)", "Kategori di Sumbu X (Warna = Tahun)"], 
                                                       horizontal=True, key=f"switch_rowcol_{idx}")
                                
                                if mode_grafik == "Tahun di Sumbu X (Warna = Kategori)":
                                    var_x, var_color = 'Tahun', 'Kategori'
                                    map_warna_aktif = new_color_map # Pakai custom warna kamu!
                                else:
                                    var_x, var_color = 'Kategori', 'Tahun'
                                    map_warna_aktif = {} # Balik ke default kalau warnain tahun

                                # 4. PLOTTING GRAFIK
                                if n_type == "Bar":
                                    if n_orientasi == "Horizontal":
                                        fig = px.bar(res_plot, x='Nilai', y=var_x, color=var_color,
                                                    orientation='h', barmode='group', text_auto='.2f',
                                                    color_discrete_map=map_warna_aktif)
                                        fig.update_yaxes(autorange="reversed")
                                        l_pake = 200
                                    else:
                                        fig = px.bar(res_plot, x=var_x, y='Nilai', color=var_color,
                                                    barmode='group', text_auto='.2f',
                                                    color_discrete_map=map_warna_aktif)
                                        fig.update_traces(marker=dict(cornerradius=10))
                                        l_pake = 80

                                elif n_type == "Line":
                                    fig = px.line(res_plot, x=var_x, y='Nilai', color=var_color,
                                                markers=True, color_discrete_map=map_warna_aktif)
                                    fig.update_xaxes(type='category') 
                                    l_pake = 80

                                else:  # Box Plot
                                    fig = px.box(res_plot, x=var_x, y='Nilai', color=var_color,
                                                color_discrete_map=map_warna_aktif)
                                    l_pake = 80

                                # Update spacing biar rapi
                                fig.update_layout(bargap=0.1, bargroupgap=0.05)
                                
                                # --- 5. ANOTASI AI (Hanya jika posisi 'Dalam Grafik') ---
                                if isi_ai and opt_posisi == "Dalam Grafik":
                                    lebar_ai = ch.get('ai_w', 500)
                                    align_ai = ch.get('ai_align', 'center')
                                    jarak_ai = ch.get('ai_y', -0.15)  # naikkan ke -0.15
                                    pakai_kotak = ch.get('ai_border', False)
                                    kar_per_baris = max(1, int((lebar_ai - 20) / (size_pake * 0.55)))
                                    wrapped_text = "<br>".join(textwrap.wrap(isi_ai, width=kar_per_baris))
                                    if align_ai == "left":
                                        x_pos, xanchor = 0.02, "left"
                                    elif align_ai == "right":
                                        x_pos, xanchor = 0.98, "right"
                                    else:
                                        x_pos, xanchor = 0.5, "center"
                                    fig.add_annotation(
                                        text=wrapped_text, xref="paper", yref="paper",
                                        x=x_pos, xanchor=xanchor, y=jarak_ai, showarrow=False, align=align_ai,
                                        font=dict(family=n_font, size=size_pake, color=c_txt),
                                        bgcolor=ch.get('ai_bg_col', '#FFFFFF') if pakai_kotak else "rgba(0,0,0,0)",
                                        bordercolor=ch.get('ai_line_col', '#000000') if pakai_kotak else "rgba(0,0,0,0)",
                                        borderwidth=ch.get('ai_line_w', 1) if pakai_kotak else 0,
                                        borderpad=10
                                    )
                                    # pastikan margin bawah cukup
                                    fig.update_layout(margin=dict(b=170))

                                # --- 6. FINAL LAYOUT ---
                                fig.update_layout(
                                    title={
                                        'text': wrap_judul(n_title, width=30),
                                        'x': 0.5,
                                        'y': 0.95,           # Judul di posisi atas pas tengah
                                        'xanchor': 'center',
                                        'yanchor': 'top',
                                        'font': {'family': n_font, 'size': size_pake + 4, 'color': c_txt}
                                    },
                                    # t=170 adalah jarak agar grafik turun ke bawah, tidak nabrak judul
                                    # r=50 memperkecil margin kanan agar grafik melebar ke samping
                                    margin=dict(l=l_pake, r=50, t=90, b=b_marg),
                                   
                                    plot_bgcolor='rgba(0,0,0,0)', # Bikin background area grafik transparan (bersih)
                                    paper_bgcolor=c_bg,           # Warna kertas sesuai pilihan session state
                                    font=dict(family=n_font, size=n_size, color=c_txt),
                                   
                                    # Legend ditaruh di ATAS secara HORIZONTAL (Kunci tampilan pro)
                                    legend=dict(
                                        orientation="h",
                                        yanchor="bottom",
                                        y=1.02,
                                        xanchor="center",
                                        x=0.5,
                                        font=dict(family=n_font, color=c_txt),
                                        title=None
                                    ),
                                   
                                    xaxis=dict(
                                        tickangle=0,
                                        showgrid=False,           # Hilangkan garis vertikal
                                        linecolor=c_txt,          # Garis bawah sumbu X
                                        tickfont=dict(family=n_font, size=size_pake, color=c_txt),
                                        title=None
                                    ),
                                   
                                    yaxis=dict(
                                        tickformat=',.2f',
                                        gridcolor='rgba(128,128,128,0.1)', # Garis bantu horizontal tipis saja
                                        showline=False,           # Hilangkan garis vertikal sumbu Y
                                        zeroline=False,
                                        tickfont=dict(family=n_font, size=size_pake, color=c_txt),
                                        title=None                # Hilangkan label "Nilai" biar lebih clean
                                    )
                                )

                                # Paksa Sumbu X Lurus
                                fig.update_xaxes(tickangle=0)

                                # --- 7. TAMPILKAN ---
                                st.plotly_chart(fig, use_container_width=True)

                                # --- 5. KONTROL INTERAKTIF ---
                                st.write("---")
                               
                                # Jika bar, munculkan pilihan orientasi
                                if n_type == "Bar":
                                    n_orientasi_baru = st.selectbox("↔️ Pilih Orientasi Batang:", ["Vertical", "Horizontal"],
                                                               index=0 if n_orientasi == "Vertical" else 1, key=f"orient_{id_unik}")
                                    if n_orientasi_baru != n_orientasi:
                                        ch['orientasi'] = n_orientasi_baru
                                        st.rerun()

                                c_pos, c_ai = st.columns([1, 1])
                                pilihan_posisi = c_pos.radio("📍 Posisi Narasi:", ["Bawah", "Dalam Grafik"],
                                                           index=0 if opt_posisi == "Bawah" else 1, key=f"radio_pos_{idx}", horizontal=True)
                               
                                if pilihan_posisi != opt_posisi:
                                    st.session_state[f"pos_ai_{idx}"] = pilihan_posisi
                                    st.rerun()

                                if c_ai.button(f"✨ Tanya Gemini", key=f"btn_gemini_{idx}", width='stretch'):
                                    if not res.empty:
                                        # Cari nilai tertinggi dan terendah
                                        r_max = res.loc[res['Nilai'].idxmax()]
                                        r_min = res.loc[res['Nilai'].idxmin()]
                                        
                                        # BIKIN PROMPT AI LEBIH LENGKAP DENGAN JUDUL GRAFIK (n_title)
                                        bahan = (
                                            f"Judul Grafik: '{n_title}'. "
                                            f"Ini adalah grafik tentang {label_y_desc} berdasarkan kategori {x_f}. "
                                            f"Data tertinggi ada pada {r_max[x_f]} dengan nilai {r_max['Nilai']:.2f}. "
                                            f"Sedangkan data terendah ada pada {r_min[x_f]} dengan nilai {r_min['Nilai']:.2f}."
                                        )
                                        
                                        with st.spinner("🤖 Menganalisis..."):
                                            jawaban = core.minta_interpretasi_gemini(ringkasan_data=bahan, nama_survei=snama)
                                            st.session_state[id_unik] = jawaban
                                            st.rerun()

                                if isi_ai and pilihan_posisi == "Bawah":
                                    st.info(isi_ai)

                                isi_baru = st.text_area("📝 Edit Narasi:", value=st.session_state.get(id_unik, ""), key=f"input_area_{id_unik}", height=120)
                                if isi_baru != st.session_state.get(id_unik, ""):
                                                st.session_state[id_unik] = isi_baru
                                                ch['interpretasi_saved'] = isi_baru 
                                                st.rerun()

                            except Exception as e:
                                st.error(f"⚠️ Waduh, ada error pas olah data: {e}")

    st.write("---")
    if st.button("➕ Tambah Grafik Baru", width='stretch'):
        charts.append({"type": "Bar", "x": "", "agg": "Jumlah (Count)", "years": []})
        st.rerun()

elif st.session_state.halaman == "Detail":
    st.title("💾 Manajemen Detail Data")
   
    # 1. Pilih Survei & Tahun
    c_s, c_y = st.columns(2)
    with c_s:
        daftar_s = core.ambil_daftar_survei()
        s_pilih = st.selectbox("Pilih Survei:", daftar_s if daftar_s else ["Kosong"], format_func=lambda x: x.upper())
   
    years = []
    if s_pilih != "Kosong":
        path_s = os.path.join("data_survei", s_pilih)
        years = sorted([f.replace(".parquet", "") for f in os.listdir(path_s) if f.endswith(".parquet")])
   
    with c_y:
        y_pilih = st.selectbox("Pilih Tahun:", years if years else ["Belum ada data"])

    if y_pilih != "Belum ada data":
        df_view = core.ambil_info_data(s_pilih, y_pilih)
        st.info(f"📋 Dataset ini memiliki **{df_view.shape[0]}** baris dan **{df_view.shape[1]}** kolom.")
        st.dataframe(df_view.head(10), width='stretch')
       
        st.divider()
       
        # 2. FITUR EDIT & REPLACE
        t1, t2, t3 = st.tabs(["✂️ Hapus Kolom", "🔄 Unggah Ulang (Replace)", "🗑️ Hapus Dataset"])
       
        with t1:
            kolom_hapus = st.multiselect("Pilih variabel untuk dibuang:", df_view.columns.tolist(), key="ms_kolom")
            if st.button("Proses Hapus Kolom", type="primary", width='stretch'):
                if kolom_hapus:
                    st.session_state.kolom_target_hapus = kolom_hapus
                    st.session_state.edit_survei = s_pilih
                    st.session_state.edit_tahun = y_pilih
                    st.session_state.dialog_aktif = "konfirmasi_edit"
                    st.rerun()
       
        with t2:
            st.write(f"Mengganti data **{s_pilih.upper()} {y_pilih}** dengan file baru.")
            file_baru = st.file_uploader("Pilih file baru (.csv, .sav, .xlsx):", type=['csv', 'sav', 'xlsx'], key="replace_file")
            if st.button("Konfirmasi Replace Data", width='stretch'):
                if file_baru:
                    sukses, pesan = core.simpan_data_upload(s_pilih, file_baru, y_pilih)
                    st.session_state.upload_sukses = sukses
                    st.session_state.upload_pesan = pesan
                    st.session_state.dialog_aktif = "status_upload"
                    st.rerun()
       
        with t3:
            st.write("Menghapus seluruh file data untuk tahun ini.")
            if st.button("Hapus Seluruh Dataset Tahun Ini", type="primary", width='stretch'):
                st.session_state.edit_survei = s_pilih
                st.session_state.edit_tahun = y_pilih
                st.session_state.dialog_aktif = "hapus_dataset"
                st.rerun()

elif st.session_state.halaman == "Kelola":
    st.title("⚙️ Kelola Survei")
    st.write("Di sini Anda dapat mengelola metadata atau menghapus survei secara keseluruhan.")
    
    daftar_s = core.ambil_daftar_survei()
    
    if not daftar_s:
        st.info("Belum ada survei yang terdaftar.")
    else:
        for s_nama in daftar_s:
            with st.container(border=True):
                st.subheader(f"📌 {s_nama.upper()}")
                
                c1, c2, c3 = st.columns([2, 1, 1])
                
                with c1:
                    st.write(f"Survei aktif: {s_nama}")
                
                with c2:
                    # Tombol menuju halaman Edit Kamus / Metadata
                    if st.button("📝 Edit Kamus Data", key=f"edit_meta_{s_nama}", use_container_width=True):
                        pindah_halaman("EditMetadata", target_edit=s_nama)
                
                with c3:
                    # INI DIA TOMBOL PEMICU HAPUSNYA!
                    if st.button("🗑️ Hapus Survei", key=f"del_srv_{s_nama}", type="primary", use_container_width=True):
                        # Kita set nama survei yang mau dihapus
                        st.session_state.target_hapus = s_nama
                        # Kita panggil dialognya!
                        st.session_state.dialog_aktif = "hapus"
                        st.rerun()

elif st.session_state.halaman == "EditMetadata":
    s_nama = st.session_state.target_edit_metadata
    st.title(f"📝 Kamus Data: {s_nama.upper()}")
   
    # 1. Pilih Tahun yang ingin dikelola kamusnya
    path_s = os.path.join("data_survei", s_nama)
    years = sorted([f.replace(".parquet", "") for f in os.listdir(path_s) if f.endswith(".parquet")])
   
    if not years:
        st.warning("Belum ada data yang diunggah untuk survei ini.")
        if st.button("Kembali"):
            st.session_state.halaman = "Kelola"
            st.rerun()
    else:
        y_edit = st.selectbox("Pilih Tahun untuk Diedit Kamusnya:", years)
       
        # Fitur Salin Metadata (Cloning)
        with st.expander("👯 Salin Kamus dari Tahun Lain"):
            other_years = [y for y in years if y != y_edit]
            y_sumber = st.selectbox("Pilih Tahun Sumber:", ["Pilih..."] + other_years)
           
            if st.button("Terapkan Salinan", width='stretch'):
                if y_sumber != "Pilih...":
                    # Simpan informasi ke session state untuk pop-up
                    st.session_state.salin_sumber = y_sumber
                    st.session_state.salin_target = y_edit
                    st.session_state.dialog_aktif = "salin_metadata"
                    st.rerun()
                else:
                    st.warning("Pilih tahun sumber terlebih dahulu.")

        st.divider()
       
        # 2. Form Edit Kamus - Versi Perbaikan
        df_sample = pd.read_parquet(os.path.join(path_s, f"{y_edit}.parquet"))
        kamus_saat_ini = core.ambil_metadata_tahunan(s_nama, y_edit)
       
        new_kamus = {}
        st.write(f"Mengedit variabel untuk data tahun **{y_edit}**:")
       
        # Header Tabel
        h1, h2, h3 = st.columns([2, 3, 1])
        h1.markdown("**Nama Asli (Raw)**")
        h2.markdown("**Alias (Nama di Grafik)**")
        h3.markdown("**Tampil?**")
        for col in df_sample.columns:
            if col == "Tahun": continue
           
            key_alias = f"al_{y_edit}_{col}"
            key_show = f"sh_{y_edit}_{col}"
           
            if key_alias not in st.session_state:
                st.session_state[key_alias] = kamus_saat_ini.get(col, {}).get("alias", col)
            if key_show not in st.session_state:
                st.session_state[key_show] = kamus_saat_ini.get(col, {}).get("show", True)
           
            c1, c2, c3 = st.columns([2, 3, 1])
            c1.text(col)
           
            alias = c2.text_input(f"Alias {col}", key=key_alias, label_visibility="collapsed")
            show = c3.checkbox("Cek", key=key_show, label_visibility="collapsed")
           
            new_kamus[col] = {"alias": alias, "show": show}
           
        if st.button("Simpan Perubahan Kamus", type="primary", width='stretch'):
            core.simpan_metadata_tahunan(s_nama, y_edit, new_kamus)
            st.success(f"Kamus tahun {y_edit} berhasil disimpan!")














