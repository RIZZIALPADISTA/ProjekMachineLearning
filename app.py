# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Penjualan",
    page_icon="�",
    layout="wide"
)

# Fungsi untuk memuat dan membersihkan data (dengan cache agar lebih cepat)
@st.cache_data
def load_data(file_path):
    """
    Fungsi ini memuat data dari file CSV, membersihkan data sesuai kebutuhan,
    dan mengembalikan DataFrame yang sudah bersih.
    """
    try:
        # Coba baca dengan delimiter koma (default)
        df = pd.read_csv(file_path)
        # Jika hanya ada satu kolom, kemungkinan besar delimiter-nya salah
        if len(df.columns) == 1:
            st.info("Mencoba membaca ulang file dengan delimiter titik koma (;)")
            df = pd.read_csv(file_path, delimiter=';')
            
    except FileNotFoundError:
        st.error(f"File tidak ditemukan di path: {file_path}")
        st.info(f"Pastikan nama file sudah benar dan berada di folder yang sama dengan 'app.py'.")
        return None
    except Exception as e:
        st.error(f"Terjadi error saat membaca file: {e}")
        return None

    # --- DEFINISIKAN NAMA KOLOM PENTING DI SINI ---
    PRODUCT_COL = 'Jenis Produk'
    DATE_COL = 'Tanggal'
    PRICE_COL = 'Harga'
    QUANTITY_COL = 'Jumlah Order'
    TOTAL_COL = 'Total' # Menggunakan kolom 'Total' dari file
    
    # --- Pemeriksaan Kolom Terpusat ---
    required_cols = [PRODUCT_COL, DATE_COL, PRICE_COL, QUANTITY_COL, TOTAL_COL]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"Error Kritis: Kolom berikut tidak ditemukan di file CSV Anda: {', '.join(missing_cols)}")
        st.warning("Nama-nama kolom yang tersedia di file Anda adalah:")
        st.write(df.columns.tolist())
        st.info("Silakan perbaiki nama kolom di bagian 'DEFINISIKAN NAMA KOLOM PENTING' pada kode 'app.py', lalu simpan dan refresh halaman.")
        return None

    # --- Proses Data (Setelah dipastikan semua kolom ada) ---
    try:
        # Lakukan pembersihan data menggunakan variabel
        df[PRODUCT_COL].fillna('Unknown', inplace=True)
        df[PRODUCT_COL] = df[PRODUCT_COL].str.replace('CraftLaminasi$', 'CraftLaminasi290', regex=True)
        
        df[DATE_COL] = pd.to_datetime(df[DATE_COL], dayfirst=True)
        
        # Membersihkan kolom numerik
        for col in [PRICE_COL, QUANTITY_COL, TOTAL_COL]:
             df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d,.]', '', regex=True).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
        
        # Buat kolom 'Total Pendapatan' yang bersih untuk kalkulasi dashboard
        df['Total Pendapatan'] = df[PRICE_COL] * df[QUANTITY_COL]

        return df

    except Exception as e:
        st.error(f"Terjadi error saat memproses data: {e}")
        st.info("Periksa kembali format data pada kolom yang bermasalah (misalnya: pastikan nilai di kolom harga dan jumlah adalah angka).")
        return None


# --- Mulai UI Streamlit ---

# Judul Dashboard
st.title("📊 Dashboard Analisis Penjualan Produk Cetakan")
st.markdown("Gunakan filter di samping untuk menganalisis data penjualan.")

# Ganti nama file ini jika berbeda
df = load_data("data_penjualan_produk_cetakan.csv")

# Hentikan eksekusi jika data gagal dimuat
if df is None:
    st.stop()

# --- Gunakan variabel yang sama untuk konsistensi ---
PRODUCT_COL = 'Jenis Produk'
QUANTITY_COL = 'Jumlah Order'
PRICE_COL = 'Harga'
TOTAL_COL = 'Total'
DATE_COL = 'Tanggal'

# --- Sidebar untuk Filter ---
st.sidebar.header("Filter Data Dashboard:")

unique_products = sorted(df[PRODUCT_COL].unique())
selected_products_for_dashboard = st.sidebar.multiselect(
    f"Pilih {PRODUCT_COL} untuk Dashboard:",
    options=unique_products,
    default=unique_products
)

if selected_products_for_dashboard:
    df_filtered = df[df[PRODUCT_COL].isin(selected_products_for_dashboard)]
else:
    df_filtered = df.copy()

# --- Tampilan Utama ---
st.header("Ringkasan Penjualan (Dashboard)")
total_revenue = df_filtered['Total Pendapatan'].sum()
total_items_sold = df_filtered[QUANTITY_COL].sum()
total_transactions = len(df_filtered)

col1, col2, col3 = st.columns(3)
col1.metric("Total Pendapatan Terkalkulasi", f"Rp {total_revenue:,.2f}")
col2.metric("Total Produk Terjual", f"{total_items_sold:,.0f}")
col3.metric("Jumlah Transaksi", f"{total_transactions:,.0f}")

st.markdown("---")

st.header("Visualisasi Data (Dashboard)")
# Grafik 1: Bar Chart
fig_revenue_by_product = px.bar(
    df_filtered.groupby(PRODUCT_COL)['Total Pendapatan'].sum().reset_index(),
    x=PRODUCT_COL,
    y='Total Pendapatan',
    title=f'<b>Total Pendapatan per {PRODUCT_COL}</b>',
    template='plotly_white'
)
# Grafik 2: Pie Chart
fig_sold_by_product = px.pie(
    df_filtered,
    names=PRODUCT_COL,
    values=QUANTITY_COL,
    title=f'<b>Persentase Jumlah Terjual per {PRODUCT_COL}</b>',
    hole=.3
)

left_col, right_col = st.columns(2)
left_col.plotly_chart(fig_revenue_by_product, use_container_width=True)
right_col.plotly_chart(fig_sold_by_product, use_container_width=True)

if DATE_COL in df_filtered.columns:
    daily_sales = df_filtered.groupby(df_filtered[DATE_COL].dt.date)['Total Pendapatan'].sum().reset_index()
    fig_daily_sales = px.line(
        daily_sales,
        x=DATE_COL,
        y='Total Pendapatan',
        title='<b>Tren Pendapatan Harian</b>',
        labels={DATE_COL: 'Tanggal', 'Total Pendapatan': 'Total Pendapatan (Rp)'},
        template='plotly_white',
        markers=True
    )
    st.plotly_chart(fig_daily_sales, use_container_width=True)

st.markdown("---")


# --- FITUR YANG DIPERBARUI: Pilih & Lihat Detail Produk ---
st.header("🔍 Pilih & Lihat Detail Produk")

# Input teks untuk memfilter daftar produk
search_term = st.text_input(
    "Ketik nama produk untuk mencari:",
    placeholder="Contoh: Stiker, Kartu Nama"
)

# Filter daftar produk berdasarkan input pencarian
if search_term:
    # Pencarian tidak sensitif huruf besar/kecil
    filtered_options = [p for p in unique_products if search_term.lower() in p.lower()]
else:
    filtered_options = unique_products

# Pilihan ganda (multiselect) dengan daftar yang sudah difilter
selected_items_for_detail = st.multiselect(
    "Pilih satu atau lebih produk untuk melihat detail transaksinya:",
    options=filtered_options,
    default=filtered_options if search_term else ([unique_products[0]] if unique_products else [])
)


if selected_items_for_detail:
    # Filter dataframe untuk semua produk yang dipilih
    detail_df = df[df[PRODUCT_COL].isin(selected_items_for_detail)].copy()
    
    # Buat dataframe terpisah untuk tampilan agar data asli tetap numerik
    display_df = detail_df.copy()
    
    # Atur format kolom mata uang agar lebih rapi
    display_df[PRICE_COL] = display_df[PRICE_COL].apply(lambda x: f"Rp {x:,.2f}")
    display_df[TOTAL_COL] = display_df[TOTAL_COL].apply(lambda x: f"Rp {x:,.2f}")

    # Pilih kolom yang akan ditampilkan, termasuk 'Jenis Produk' agar tidak bingung
    cols_to_show = [DATE_COL, PRODUCT_COL, QUANTITY_COL, PRICE_COL, TOTAL_COL]
    st.dataframe(
        display_df[cols_to_show].sort_values(by=[DATE_COL, PRODUCT_COL], ascending=False),
        use_container_width=True
    )


st.markdown("---")
st.header("Tabel Data Lengkap (Sesuai Filter Dashboard)")
st.dataframe(df_filtered)
