import os
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from google.colab import files

# =====================================================================
# 1. MENYIAPKAN DAN MENGGABUNGKAN DATA (SPATIAL JOIN)
# =====================================================================
shp_file = "KOTA_BENGKULU.shp"
csv_file = "Data_Hujan_Kecamatan.csv"

if os.path.exists(shp_file) and os.path.exists(csv_file):
    print("[PROSES] Membaca dan mengintegrasikan data...")

    # Membaca Data Spasial (.shp)
    bengkulu_map = gpd.read_file(shp_file)
    bengkulu_map.columns = bengkulu_map.columns.str.lower()
    bengkulu_map = bengkulu_map[bengkulu_map.geometry.notnull() & ~bengkulu_map.geometry.is_empty]

    # Membaca Data Excel (.csv) dengan fleksibilitas delimiter
    try:
        df_hujan = pd.read_csv(csv_file, delimiter=",")
        if len(df_hujan.columns) <= 1: raise ValueError
    except:
        df_hujan = pd.read_csv(csv_file, delimiter=";")

    df_hujan.columns = df_hujan.columns.astype(str).str.strip()

    # Deteksi otomatis kolom utama pada CSV
    col_kec_csv = [col for col in df_hujan.columns if 'kec' in col.lower() or 'kel' in col.lower()][0]
    col_hujan_csv = [col for col in df_hujan.columns if 'hujan' in col.lower() or 'rr' in col.lower()][0]

    # Normalisasi teks untuk pencocokan data (Join Key)
    df_hujan['Kecamatan_Clean'] = df_hujan[col_kec_csv].astype(str).str.strip().str.upper()
    df_hujan['Hujan_Clean'] = pd.to_numeric(df_hujan[col_hujan_csv].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    kolom_kec_shp = [col for col in bengkulu_map.columns if 'namobj' in col or 'kec' in col or 'name' in col][0]
    bengkulu_map['match_key'] = bengkulu_map[kolom_kec_shp].astype(str).str.strip().str.upper().str.replace(' ', '')
    df_hujan['match_key'] = df_hujan['Kecamatan_Clean'].str.replace(' ', '')

    # Proses penggabungan akhir
    peta_final = bengkulu_map.merge(df_hujan, on='match_key', how='left')
    peta_final['Hujan_Clean'] = peta_final['Hujan_Clean'].fillna(0)

    # =====================================================================
    # 2. BLOK GAMBAR 1: PETA DISTRIBUSI SPASIAL CHOROPLETH
    # =====================================================================
    print("\n[PROSES] Membuat Output 1: Peta Spasial...")
    fig1, ax1 = plt.subplots(figsize=(11, 9), facecolor='#ffffff')

    peta_final.plot(
        column='Hujan_Clean',
        cmap='Blues',
        edgecolor='#1e293b',
        linewidth=1.2,
        legend=True,
        legend_kwds={
            'label': "Intensitas Akumulasi Curah Hujan Tahunan (mm/tahun)",
            'orientation': "horizontal",
            'pad': 0.05,
            'shrink': 0.7
        },
        ax=ax1
    )

    # Menambahkan label teks nama kecamatan & nilai hujan di dalam peta
    for idx, row in peta_final.iterrows():
        if row.geometry and not row.geometry.is_empty:
            pt = row.geometry.representative_point()
            if not pd.isna(pt.x) and not pd.isna(pt.y):
                nama_lokal = row[kolom_kec_shp]
                nilai_hujan = row['Hujan_Clean']
                label_peta = f"{nama_lokal}\n({nilai_hujan:.0f} mm)" if nilai_hujan > 0 else f"{nama_lokal}"
                ax1.text(pt.x, pt.y, label_peta, horizontalalignment='center', fontsize=8, color='#0f172a', weight='bold')

    ax1.set_title("PETA DISTRIBUSI SPASIAL CURAH HUJAN TAHUNAN\nKECAMATAN KOTA BENGKULU", fontsize=12, weight='bold', pad=15)
    ax1.text(0.02, 0.95, '▲\nN', transform=ax1.transAxes, ha='center', va='center', fontsize=12, weight='bold', color='#1e293b')
    ax1.axis('off')
    plt.tight_layout()

    output_peta = "1_peta_curah_hujan_bengkulu.png"
    plt.savefig(output_peta, dpi=300, bbox_inches='tight')
    plt.show()  # Menampilkan peta secara mandiri

    # =====================================================================
    # 3. BLOK GAMBAR 2: GRAFIK BATANG PERBANDINGAN NILAI
    # =====================================================================
    print("\n[PROSES] Membuat Output 2: Grafik Batang Perbandingan...")

    # Urutkan dataframe khusus untuk visualisasi grafik (dari terkecil ke terbesar agar di grafik horizontal urut top-down)
    df_grafik = peta_final.drop_duplicates(subset=['match_key']).sort_values(by='Hujan_Clean', ascending=True)

    fig2, ax2 = plt.subplots(figsize=(11, 6), facecolor='#ffffff')

    # Membuat gradasi warna bar agar selaras dengan skema warna peta
    gradasi_warna = plt.cm.Blues(df_grafik['Hujan_Clean'] / (df_grafik['Hujan_Clean'].max() if df_grafik['Hujan_Clean'].max() > 0 else 1))

    # Plotting grafik batang horizontal
    bars = ax2.barh(df_grafik[kolom_kec_shp], df_grafik['Hujan_Clean'], color=gradasi_warna, edgecolor='#1e3a8a', height=0.6)

    # Menaruh label nilai presisi angka di ujung luar setiap batang grafik
    for bar in bars:
        width = bar.get_width()
        if width > 0:
            ax2.text(width + 15, bar.get_y() + bar.get_height()/2, f'{width:,.0f} mm',
                     va='center', fontsize=9, weight='bold', color='#1e293b')

    ax2.set_title("PERBANDINGAN CURAH HUJAN TAHUNAN ANTAR KECAMATAN\nKOTA BENGKULU", fontsize=12, weight='bold', pad=15, color='#1e3a8a')
    ax2.set_xlabel("Volume Curah Hujan (mm/tahun)", fontsize=10, weight='bold')
    ax2.set_ylabel("Kecamatan", fontsize=10, weight='bold')
    ax2.grid(axis='x', linestyle='--', alpha=0.4)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    plt.tight_layout()

    output_grafik = "2_grafik_curah_hujan_bengkulu.png"
    plt.savefig(output_grafik, dpi=300, bbox_inches='tight')
    plt.show()  # Menampilkan grafik secara mandiri

    # =====================================================================
    # 4. PROSES DOWNLOAD OTOMATIS KEDUA BERKAS GAMBAR
    # =====================================================================
    print("\n[SUKSES] Mengunduh kedua dokumen gambar hasil analisis ke komputer Anda...")
    files.download(output_peta)
    files.download(output_grafik)

else:
    print("[GAGAL] Pastikan file 'KOTA_BENGKULU.shp' dan 'Data_Hujan_Kecamatan.csv' ada di folder kiri!")