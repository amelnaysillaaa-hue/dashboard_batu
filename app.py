import streamlit as st
import core_logic as core
import pandas as pd
import plotly.express as px
import os
import textwrap

# ==================== KONFIGURASI HALAMAN ====================
st.set_page_config(page_title="Dashboard Statistik Batu", layout="wide")

# ==================== FUNGSI NAVIGASI & STATE ====================
def inisialisasi_state():
    params = st.query_params
    if 'halaman' not in st.session_state:
        st.session_state.halaman = params.get("p", "Landing")
    if 'survei_aktif' not in st.session_state:
        st.session_state.survei_aktif = params.get("s", None)
    if 'target_edit_metadata' not in st.session_state:
        st.session_state.target_edit_metadata = params.get("t", None)
    if 'dialog_aktif' not in st.session_state:
        st.session_state.dialog_aktif = None
    if 'sukses_proses' not in st.session_state:
        st.session_state.sukses_proses = False

def pindah_halaman(nama_halaman, survei=None, target_edit=None):
    st.session_state.halaman = nama_halaman
    st.session_state.survei_aktif = survei
    st.session_state.target_edit_metadata = target_edit
    new_params = {"p": nama_halaman}
    if survei:
        new_params["s"] = survei
    if target_edit:
        new_params["t"] = target_edit
    st.query_params.clear()
    for k, v in new_params.items():
        st.query_params[k] = v
    st.rerun()

def wrap_judul(text, width=30):
    if not text:
        return ""
    return "<br>".join(textwrap.wrap(text, width=width))

# ==================== STYLE & FONT ====================
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Lexend:wght@400;700&family=Montserrat:wght@400;700&family=Poppins:wght@400;700&family=Roboto:wght@400;700&family=Open+Sans:wght@400;700&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"] { font-size: 14px; }
    [data-testid="stSidebar"] { font-size: 13px; }
    .stButton>button { font-size: 12px; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==================== INISIALISASI ====================
core.inisialisasi_sistem()
inisialisasi_state()

# ==================== DIALOG POP-UP ====================
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

# Pemicu dialog
if st.session_state.dialog_aktif == "tambah":
    pop_tambah_survei()
elif st.session_state.dialog_aktif == "hapus":
    pop_hapus_survei()
elif st.session_state.dialog_aktif == "status_upload":
    pop_status_upload()
elif st.session_state.dialog_aktif == "konfirmasi_edit":
    pop_konfirmasi_edit()
elif st.session_state.dialog_aktif == "hapus_dataset":
    pop_hapus_dataset_tahun()
elif st.session_state.dialog_aktif == "salin_metadata":
    pop_salin_metadata()

# ==================== SIDEBAR ====================
st.sidebar.title("🗂️ Menu Utama")
if st.sidebar.button("🏠 Beranda", width='stretch'):
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

# ==================== HALAMAN LANDING ====================
if st.session_state.halaman == "Landing":
    st.title("🏔️ Selamat Datang")
    st.header("Dashboard Visualisasi Data Statistik Kota Batu")
    st.markdown("Dashboard ini dirancang untuk mempermudah pembuatan grafik hasil survei secara otomatis.")
    st.info(f"Terdapat **{len(daftar)}** jenis survei yang tersimpan dalam sistem.")

# ==================== HALAMAN VISUALISASI ====================
elif st.session_state.halaman == "Visualisasi":
    snama = st.session_state.survei_aktif
    if not snama:
        st.warning("⚠️ Silakan pilih survei di sidebar.")
        st.stop()

    # Load konfigurasi grafik
    if 'last_loaded' not in st.session_state or st.session_state.last_loaded != snama:
        config = core.ambil_viz_config(snama)
        st.session_state.viz_state = config if config else {"charts": []}
        st.session_state.last_loaded = snama

    st.title(f"📊 Dashboard Visualisasi: {snama.upper()}")

    # Folder data survei
    path_s = os.path.join("data_survei", snama)
    os.makedirs(path_s, exist_ok=True)

    # --- FITUR INPUT DATA MANUAL (SPREADSHEET) ---
    with st.expander("📝 Input Data Manual (Isi Langsung)", expanded=False):
        # --- EDITABLE DATA TABLE (SEMUA TAHUN) ---
        st.markdown("---")
        st.markdown("**📋 Data Semua Tahun (Klik sel untuk edit langsung)**")
        
        # Gabungkan semua data dari semua tahun
        all_data = []
        if os.path.exists(path_s):
            tahun_list = sorted([f.replace(".parquet", "") for f in os.listdir(path_s) if f.endswith(".parquet")])
            for th in tahun_list:
                df_th = pd.read_parquet(os.path.join(path_s, f"{th}.parquet"))
                if 'Kategori' in df_th.columns and 'Nilai' in df_th.columns:
                    df_th = df_th[['Kategori', 'Nilai']].copy()
                    df_th['Tahun'] = th
                    all_data.append(df_th)
                else:
                    if len(df_th.columns) >= 2:
                        df_th = df_th.iloc[:, :2].copy()
                        df_th.columns = ['Kategori', 'Nilai']
                        df_th['Tahun'] = th
                        all_data.append(df_th)
        if all_data:
            df_combined = pd.concat(all_data, ignore_index=True)
            df_combined = df_combined[['Tahun', 'Kategori', 'Nilai']]
            
            edited_df = st.data_editor(
                df_combined,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Tahun": st.column_config.NumberColumn("Tahun", min_value=2000, max_value=2030, step=1),
                    "Kategori": st.column_config.TextColumn("Kategori"),
                    "Nilai": st.column_config.NumberColumn("Nilai", format="%.2f"),
                },
                key=f"data_editor_{snama}"
            )
            
            col_save, col_refresh = st.columns(2)
            with col_save:
                if st.button("💾 Simpan Semua Perubahan", type="primary", use_container_width=True):
                    for th in tahun_list:
                        core.hapus_semua_data_tahun(snama, th)
                    for tahun, group in edited_df.groupby('Tahun'):
                        df_to_save = group[['Kategori', 'Nilai']].copy()
                        folder = os.path.join("data_survei", snama)
                        os.makedirs(folder, exist_ok=True)
                        file_path = os.path.join(folder, f"{tahun}.parquet")
                        df_to_save.to_parquet(file_path, index=False)
                    st.success("✅ Semua perubahan disimpan!")
                    st.session_state.last_loaded = None
                    st.rerun()
            with col_refresh:
                if st.button("🔄 Refresh Data", use_container_width=True):
                    st.session_state.last_loaded = None
                    st.rerun()
        else:
            st.info("Belum ada data. Silakan tambah data di atas atau upload file.")

    # --- UNGGAH DATA (OTOMATIS DETEKSI TAHUN) ---
    col_up, col_sv = st.columns([3, 1])
    with col_up.expander("⬆️ Unggah Data Baru (CSV/Excel/SAV) - Otomatis deteksi tahun"):
        f_up = st.file_uploader("Pilih file (CSV, Excel, SPSS)", type=['csv', 'sav', 'xlsx'], key="viz_up")
        if st.button("Konfirmasi Unggah", width='stretch'):
            if f_up:
                sukses, pesan = core.simpan_data_upload_auto(snama, f_up)
                if sukses:
                    st.session_state.upload_sukses = sukses
                    st.session_state.upload_pesan = pesan
                    st.session_state.dialog_aktif = "status_upload"
                    st.rerun()
                else:
                    st.error(pesan)
    with col_sv:
        if st.button("💾 Simpan Dashboard", width='stretch', type="primary"):
            core.simpan_viz_config(snama, st.session_state.viz_state)
            st.success("Tersimpan!")
    st.divider()

    # --- FUNGSI MEMUAT SEMUA DATA (OTOMATIS) ---
    def load_all_data(survey_name):
        folder = os.path.join("data_survei", survey_name)
        all_dfs = []
        for fname in os.listdir(folder):
            if fname.endswith(".parquet"):
                tahun = fname.replace(".parquet", "")
                df = pd.read_parquet(os.path.join(folder, fname))
                meta = core.ambil_metadata_tahunan(survey_name, tahun)
                alias_map = {k: v.get('alias', k) for k, v in meta.items()}
                df = df.rename(columns=alias_map)
                df['Tahun'] = str(tahun)
                all_dfs.append(df)
        if all_dfs:
            return pd.concat(all_dfs, ignore_index=True)
        return pd.DataFrame()

    # --- RENDER GRAFIK ---
    charts = st.session_state.viz_state["charts"]

    for i in range(0, len(charts), 2):
        row_cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(charts):
                with row_cols[j]:
                    with st.container(border=True):
                        ch = charts[idx]
                        id_unik = f"{snama}_viz_{idx}"
                        if id_unik not in st.session_state:
                            st.session_state[id_unik] = ch.get('interpretasi_saved', "")

                        with st.expander(f"⚙️ Pengaturan Grafik {idx+1}", expanded=not ch.get('has_config', False)):
                            n_title = st.text_input("Judul Grafik", value=ch.get('title', f"Grafik {idx+1}"), key=f"title_{idx}")
                            n_type = st.selectbox("Tipe Grafik", ["Bar", "Line", "Box"],
                                                  index=["Bar", "Line", "Box"].index(ch.get('type', 'Bar')),
                                                  key=f"type_{idx}")
                            list_agg = ["Jumlah (Count)", "Rata-rata (Mean)", "Total (Sum)", "Nilai Asli (Value)"]
                            n_agg = st.selectbox("Fungsi Agregasi", list_agg,
                                                 index=list_agg.index(ch.get('agg', 'Jumlah (Count)')),
                                                 key=f"agg_{idx}")
                            mode_grafik = st.radio("🔄 Tampilan:",
                                                   ["Tahun di Sumbu X (Warna = Kategori)",
                                                    "Kategori di Sumbu X (Warna = Tahun)"],
                                                   horizontal=True, key=f"switch_{idx}")
                            n_orientasi = "Vertical"
                            if n_type == "Bar":
                                n_orientasi = st.selectbox("↔️ Orientasi Batang", ["Vertical", "Horizontal"],
                                                           index=0 if ch.get('orientasi', 'Vertical') == "Vertical" else 1,
                                                           key=f"orient_{idx}")
                            st.markdown("**🎨 Tampilan**")
                            list_font = ["Arial", "Courier New", "Verdana", "Times New Roman", "Comic Sans MS", "Lexend", "Hanken Grotesk", "Montserrat", "Poppins", "Roboto", "Open Sans"]
                            n_font = st.selectbox("Font", list_font,
                                                  index=list_font.index(ch.get('font_family', 'Arial')) if ch.get('font_family') in list_font else 0,
                                                  key=f"font_{idx}")
                            n_size = st.number_input("Ukuran Font", 8, 24, int(ch.get('font_size', 12)), key=f"size_{idx}")
                            c_txt = st.color_picker("Warna Teks", ch.get('color_txt', '#000000'), key=f"txtcol_{idx}")
                            c_bg = st.color_picker("Warna Latar", ch.get('color_bg', '#FFFFFF'), key=f"bgcol_{idx}")
                            st.markdown("**📍 Posisi Legend**")
                            legend_position = st.selectbox(
                                "Pilih posisi legend:",
                                ["Atas (horizontal)", "Bawah (horizontal)", "Kanan (vertikal)", "Kiri (vertikal)"],
                                index=["Atas (horizontal)", "Bawah (horizontal)", "Kanan (vertikal)", "Kiri (vertikal)"].index(ch.get('legend_position', "Atas (horizontal)")),
                                key=f"legend_pos_{idx}"
                            )
                            st.markdown("**📝 Teks Interpretasi**")
                            use_border = st.checkbox("Pakai kotak pembatas", value=ch.get('ai_border', False), key=f"border_{idx}")
                            if use_border:
                                c_brd_bg = st.color_picker("Warna isi kotak", ch.get('ai_bg_col', '#FFFFFF'), key=f"aibg_{idx}")
                                c_brd_line = st.color_picker("Warna garis", ch.get('ai_line_col', '#000000'), key=f"ailine_{idx}")
                                v_brd_width = st.number_input("Tebal garis", 0, 5, ch.get('ai_line_w', 1), key=f"aiw_{idx}")
                            else:
                                c_brd_bg, c_brd_line, v_brd_width = "#FFFFFF", "#000000", 1
                            v_jarak = st.slider("Jarak teks dari grafik (Y)", -0.8, -0.05, float(ch.get('ai_y', -0.2)), key=f"aiy_{idx}")
                            v_align = st.selectbox("Rata teks", ["left", "center", "right"],
                                                   index=["left", "center", "right"].index(ch.get('ai_align', 'left')),
                                                   key=f"align_{idx}")
                            v_lebar = st.slider("Lebar kotak teks", 200, 1000, int(ch.get('ai_w', 500)), key=f"aiw2_{idx}")

                            ch.update({
                                'title': n_title, 'type': n_type, 'agg': n_agg,
                                'orientasi': n_orientasi, 'mode_switch': mode_grafik,
                                'font_family': n_font, 'font_size': n_size,
                                'color_txt': c_txt, 'color_bg': c_bg,
                                'ai_border': use_border, 'ai_bg_col': c_brd_bg,
                                'ai_line_col': c_brd_line, 'ai_line_w': v_brd_width,
                                'ai_y': v_jarak, 'ai_align': v_align, 'ai_w': v_lebar,
                                'legend_position': legend_position, 
                                'has_config': True
                            })
                            if st.button(f"🗑️ Hapus Grafik {idx+1}", key=f"del_{idx}"):
                                charts.pop(idx)
                                st.rerun()

                        df_full = load_all_data(snama)
                        if df_full.empty:
                            st.info("Belum ada data. Silakan tambah data manual atau upload file.")
                            continue

                        numeric_cols = df_full.select_dtypes(include=['number']).columns.tolist()
                        if not numeric_cols:
                            st.error("Tidak ada kolom numerik dalam data.")
                            continue
                        nilai_col = numeric_cols[0]
                        categorical_cols = [c for c in df_full.columns if c not in numeric_cols and c != 'Tahun']
                        if not categorical_cols:
                            st.error("Tidak ada kolom kategorik (selain Tahun).")
                            continue
                        kategori_col = categorical_cols[0]

                        df_plot = df_full[[kategori_col, 'Tahun', nilai_col]].copy()
                        df_plot = df_plot.rename(columns={kategori_col: 'Kategori', nilai_col: 'Nilai'})
                        df_plot['Tahun'] = df_plot['Tahun'].astype(str)
                        df_plot['Kategori'] = df_plot['Kategori'].astype(str)
                        df_plot['Nilai'] = pd.to_numeric(df_plot['Nilai'], errors='coerce')
                        df_plot = df_plot.dropna(subset=['Nilai'])

                        agg_func = ch['agg']
                        if "Count" in agg_func:
                            df_group = df_plot.groupby(['Tahun', 'Kategori']).size().reset_index(name='Nilai')
                            label_y = "Frekuensi"
                        elif "Sum" in agg_func:
                            df_group = df_plot.groupby(['Tahun', 'Kategori'])['Nilai'].sum().reset_index()
                            label_y = "Total"
                        elif "Mean" in agg_func:
                            df_group = df_plot.groupby(['Tahun', 'Kategori'])['Nilai'].mean().reset_index()
                            label_y = "Rata-rata"
                        else:
                            df_group = df_plot[['Tahun', 'Kategori', 'Nilai']].copy()
                            label_y = "Nilai"

                        if ch.get('mode_switch', "Tahun di Sumbu X (Warna = Kategori)") == "Tahun di Sumbu X (Warna = Kategori)":
                            x_var, color_var = 'Tahun', 'Kategori'
                        else:
                            x_var, color_var = 'Kategori', 'Tahun'

                        dict_warna = ch.get('color_map', {})
                        unique_kat = df_group[color_var].unique()
                        if len(unique_kat) > 0:
                            with st.expander("🎨 Warna kustom (opsional)"):
                                new_color_map = {}
                                n_cols = min(len(unique_kat), 4)
                                cols_warna = st.columns(n_cols)
                                for i, kat in enumerate(unique_kat):
                                    with cols_warna[i % n_cols]:
                                        warna_def = dict_warna.get(kat, "#636EFA")
                                        warna_pilih = st.color_picker(f"{kat}", warna_def, key=f"cp_{idx}_{i}")
                                        new_color_map[kat] = warna_pilih
                                if new_color_map != dict_warna:
                                    ch['color_map'] = new_color_map
                                    st.rerun()
                        else:
                            st.caption("Tidak ada kategori untuk diwarnai.")
                        color_map_aktif = ch.get('color_map', {})

                        if n_type == "Bar":
                            if n_orientasi == "Horizontal":
                                fig = px.bar(df_group, x='Nilai', y=x_var, color=color_var,
                                             orientation='h', barmode='group', text_auto='.2f',
                                             color_discrete_map=color_map_aktif)
                                l_margin = 50
                                fig.update_traces(marker=dict(cornerradius=10))
                            else:
                                fig = px.bar(df_group, x=x_var, y='Nilai', color=color_var,
                                             barmode='group', text_auto='.2f',
                                             color_discrete_map=color_map_aktif)
                                l_margin = 80
                                fig.update_traces(marker=dict(cornerradius=10))
                        elif n_type == "Line":
                            fig = px.line(df_group, x=x_var, y='Nilai', color=color_var,
                                          markers=True, color_discrete_map=color_map_aktif)
                            l_margin = 80
                        else:
                            fig = px.box(df_group, x=x_var, y='Nilai', color=color_var,
                                         color_discrete_map=color_map_aktif)
                            l_margin = 80

                        isi_ai = st.session_state.get(id_unik, "")
                        posisi_ai = st.session_state.get(f"pos_ai_{idx}", "Bawah")
                        bottom_margin = 80
                        if isi_ai and posisi_ai == "Dalam Grafik":
                            lebar_ai = ch.get('ai_w', 500)
                            align_ai = ch.get('ai_align', 'center')
                            jarak_ai = ch.get('ai_y', -0.15)
                            pakai_kotak = ch.get('ai_border', False)
                            kar_per_baris = max(1, int((lebar_ai - 20) / (n_size * 0.55)))
                            wrapped = "<br>".join(textwrap.wrap(isi_ai, width=kar_per_baris))
                            if align_ai == "left":
                                x_pos, xanchor = 0.02, "left"
                            elif align_ai == "right":
                                x_pos, xanchor = 0.98, "right"
                            else:
                                x_pos, xanchor = 0.5, "center"
                            fig.add_annotation(
                                text=wrapped, xref="paper", yref="paper",
                                x=x_pos, xanchor=xanchor, y=jarak_ai, showarrow=False, align=align_ai,
                                font=dict(family=n_font, size=n_size, color=c_txt),
                                bgcolor=ch.get('ai_bg_col', '#FFFFFF') if pakai_kotak else "rgba(0,0,0,0)",
                                bordercolor=ch.get('ai_line_col', '#000000') if pakai_kotak else "rgba(0,0,0,0)",
                                borderwidth=ch.get('ai_line_w', 1) if pakai_kotak else 0,
                                borderpad=10
                            )
                            bottom_margin = 170

                        legend_pos = ch.get('legend_position', "Atas (horizontal)")
                        if legend_pos == "Atas (horizontal)":
                            legend_settings = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title=None)
                            margin_dict = dict(l=l_margin, r=50, t=90, b=bottom_margin)
                        elif legend_pos == "Bawah (horizontal)":
                            legend_settings = dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, title=None)
                            bottom_margin_adj = max(bottom_margin, 100)
                            margin_dict = dict(l=l_margin, r=50, t=90, b=bottom_margin_adj)
                        elif legend_pos == "Kanan (vertikal)":
                            legend_settings = dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, title=None)
                            margin_dict = dict(l=l_margin, r=120, t=90, b=bottom_margin)
                        elif legend_pos == "Kiri (vertikal)":
                            legend_settings = dict(orientation="v", yanchor="middle", y=0.5, xanchor="right", x=-0.02, title=None)
                            margin_dict = dict(l=120, r=50, t=90, b=bottom_margin)
                        else:
                            legend_settings = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title=None)
                            margin_dict = dict(l=l_margin, r=50, t=90, b=bottom_margin)

                        fig.update_layout(
                            title={'text': wrap_judul(n_title, width=30), 'x': 0.5, 'y': 0.95,
                                   'xanchor': 'center', 'yanchor': 'top',
                                   'font': {'family': n_font, 'size': n_size + 4, 'color': c_txt}},
                            margin=margin_dict,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor=c_bg,
                            font=dict(family=n_font, size=n_size, color=c_txt),
                            legend=legend_settings,
                            xaxis=dict(tickangle=0, showgrid=False, linecolor=c_txt,
                                       tickfont=dict(family=n_font, size=n_size, color=c_txt), title=None),
                            yaxis=dict(tickformat=',.2f', gridcolor='rgba(128,128,128,0.1)',
                                       showline=False, zeroline=False,
                                       tickfont=dict(family=n_font, size=n_size, color=c_txt), title=None)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        st.write("---")
                        col_pos, col_gem = st.columns(2)
                        new_posisi = col_pos.radio("📍 Posisi Narasi:", ["Bawah", "Dalam Grafik"],
                                                   index=0 if posisi_ai == "Bawah" else 1,
                                                   key=f"pos_radio_{idx}", horizontal=True)
                        if new_posisi != posisi_ai:
                            st.session_state[f"pos_ai_{idx}"] = new_posisi
                            st.rerun()

                        if col_gem.button(f"✨ Tanya Gemini", key=f"btn_gem_{idx}", use_container_width=True):
                            if not df_group.empty:
                                max_row = df_group.loc[df_group['Nilai'].idxmax()]
                                min_row = df_group.loc[df_group['Nilai'].idxmin()]
                                prompt = (f"Judul: {n_title}. {label_y} berdasarkan {x_var} dan {color_var}. "
                                          f"Tertinggi: {max_row[x_var]} = {max_row['Nilai']:.2f} ({max_row[color_var]}). "
                                          f"Terendah: {min_row[x_var]} = {min_row['Nilai']:.2f} ({min_row[color_var]}).")
                                with st.spinner("🤖 Menganalisis..."):
                                    jawaban = core.minta_interpretasi_gemini(ringkasan_data=prompt, nama_survei=snama)
                                    st.session_state[id_unik] = jawaban
                                    st.rerun()

                        if isi_ai and new_posisi == "Bawah":
                            st.info(isi_ai)

                        teks_baru = st.text_area("📝 Edit Narasi:", value=st.session_state.get(id_unik, ""),
                                                 key=f"input_ai_{idx}", height=120)
                        if teks_baru != st.session_state.get(id_unik, ""):
                            st.session_state[id_unik] = teks_baru
                            ch['interpretasi_saved'] = teks_baru
                            st.rerun()

    st.write("---")
    if st.button("➕ Tambah Grafik Baru", width='stretch'):
        charts.append({"type": "Bar", "agg": "Jumlah (Count)", "has_config": False, "legend_position": "Atas (horizontal)"})
        st.rerun()

# ==================== HALAMAN DETAIL ====================
elif st.session_state.halaman == "Detail":
    st.title("💾 Manajemen Detail Data")
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

# ==================== HALAMAN KELOLA ====================
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
                    if st.button("📝 Edit Kamus Data", key=f"edit_meta_{s_nama}", use_container_width=True):
                        pindah_halaman("EditMetadata", target_edit=s_nama)
                with c3:
                    if st.button("🗑️ Hapus Survei", key=f"del_srv_{s_nama}", type="primary", use_container_width=True):
                        st.session_state.target_hapus = s_nama
                        st.session_state.dialog_aktif = "hapus"
                        st.rerun()

# ==================== HALAMAN EDIT METADATA ====================
elif st.session_state.halaman == "EditMetadata":
    s_nama = st.session_state.target_edit_metadata
    st.title(f"📝 Kamus Data: {s_nama.upper()}")
    path_s = os.path.join("data_survei", s_nama)
    years = sorted([f.replace(".parquet", "") for f in os.listdir(path_s) if f.endswith(".parquet")])
    if not years:
        st.warning("Belum ada data yang diunggah untuk survei ini.")
        if st.button("Kembali"):
            st.session_state.halaman = "Kelola"
            st.rerun()
    else:
        y_edit = st.selectbox("Pilih Tahun untuk Diedit Kamusnya:", years)
        with st.expander("👯 Salin Kamus dari Tahun Lain"):
            other_years = [y for y in years if y != y_edit]
            y_sumber = st.selectbox("Pilih Tahun Sumber:", ["Pilih..."] + other_years)
            if st.button("Terapkan Salinan", width='stretch'):
                if y_sumber != "Pilih...":
                    st.session_state.salin_sumber = y_sumber
                    st.session_state.salin_target = y_edit
                    st.session_state.dialog_aktif = "salin_metadata"
                    st.rerun()
                else:
                    st.warning("Pilih tahun sumber terlebih dahulu.")
        st.divider()
        df_sample = pd.read_parquet(os.path.join(path_s, f"{y_edit}.parquet"))
        kamus_saat_ini = core.ambil_metadata_tahunan(s_nama, y_edit)
        new_kamus = {}
        st.write(f"Mengedit variabel untuk data tahun **{y_edit}**:")
        h1, h2, h3 = st.columns([2, 3, 1])
        h1.markdown("**Nama Asli (Raw)**")
        h2.markdown("**Alias (Nama di Grafik)**")
        h3.markdown("**Tampil?**")
        for col in df_sample.columns:
            if col == "Tahun":
                continue
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