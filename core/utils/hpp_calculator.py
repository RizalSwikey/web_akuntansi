from decimal import Decimal
from django.db import transaction
from core.models import HppManufactureProduction, Product

def calculate_hpp_for_product(product, entries):
    awal = entries.get('AWAL')
    pembelian_list = entries.get('PEMBELIAN')
    akhir = entries.get('AKHIR')

    # 1. Hitung Data Awal
    qty_awal = Decimal(awal.quantity if awal else 0)
    harga_awal = Decimal(awal.harga_satuan if awal else 0)
    total_awal = qty_awal * harga_awal

    # 2. Hitung Data Pembelian (Neto)
    total_pembelian_neto = Decimal(0)
    total_pembelian_qty_net = Decimal(0) 

    for p in pembelian_list:
        qty_beli = Decimal(p.quantity)
        harga_beli = Decimal(p.harga_satuan)
        retur_qty = Decimal(p.retur_qty)
        diskon = Decimal(p.diskon)
        ongkir = Decimal(p.ongkir)
        
        # Hitung retur dalam rupiah
        nilai_retur_rp = retur_qty * harga_beli
        
        pembelian_bruto = qty_beli * harga_beli
        total_pembelian_item = pembelian_bruto - diskon - nilai_retur_rp + ongkir

        total_pembelian_neto += total_pembelian_item
        total_pembelian_qty_net += (qty_beli - retur_qty)

    # 3. Variabel Dasar (A)
    total_nilai_tersedia = total_awal + total_pembelian_neto
    total_qty_tersedia = qty_awal + total_pembelian_qty_net

    # Hitung Harga Beli Baru per Unit (untuk perhitungan C - FIFO)
    if total_pembelian_qty_net > 0:
        harga_beli_baru_per_unit = total_pembelian_neto / total_pembelian_qty_net
    else:
        harga_beli_baru_per_unit = Decimal(0)

    # 4. Tentukan Jumlah Terjual & Validasi Stok Akhir
    qty_akhir = Decimal(akhir.quantity if akhir else 0)
    
    if qty_akhir > total_qty_tersedia:
        qty_akhir = total_qty_tersedia # Cap agar tidak minus
        validation_error_akhir = "Periksa Kembali Catatan Penjualan/Persediaan Akhir."
    else:
        validation_error_akhir = None

    qty_terjual = total_qty_tersedia - qty_akhir

    # 5. Hitung HPP menggunakan Logika FIFO (First-In, First-Out)
    hpp_total = Decimal(0)

    if qty_terjual > qty_awal:
        # KASUS 1: Penjualan menghabiskan stok awal & mengambil stok baru
        # B = Stok Awal terjual semua
        biaya_stok_awal = total_awal 
        
        # C = Sisa penjualan diambil dari harga pembelian baru
        qty_sisa_jual = qty_terjual - qty_awal
        biaya_stok_baru = qty_sisa_jual * harga_beli_baru_per_unit
        
        hpp_total = biaya_stok_awal + biaya_stok_baru
    else:
        # KASUS 2: Penjualan sedikit, hanya mengambil dari stok awal
        hpp_total = qty_terjual * harga_awal

    # 6. Hitung Nilai Akhir (A - HPP)
    total_akhir = total_nilai_tersedia - hpp_total

    # HPP per unit (Statistik)
    if qty_terjual > 0:
        hpp_per_unit = hpp_total / qty_terjual
    else:
        hpp_per_unit = 0

    return {
        "total_awal": int(total_awal),
        "total_pembelian_neto": int(total_pembelian_neto),
        "barang_tersedia": int(total_nilai_tersedia),
        "total_akhir": int(total_akhir),
        "hpp": int(hpp_total),
        "hpp_per_unit": float(hpp_per_unit),

        "detail_awal": {
            "qty": int(qty_awal),
            "harga_satuan": int(harga_awal)
        } if awal else None,

        "detail_pembelian": {
            "qty": int(total_pembelian_qty_net),
        } if pembelian_list else None,

        "detail_akhir": {
            "qty": int(qty_akhir),
        } if akhir else None,

        "qty_terjual": int(qty_terjual),
        "validation_error_akhir": validation_error_akhir,
    }


# --- FUNGSI HELPER (INI YANG TADI HILANG) ---

def to_int(val, default=0):
    try:
        if val is None or val == "":
            return default
        return int(float(val))
    except Exception:
        return default

def to_number(x):
    if x is None:
        return Decimal(0)
    if isinstance(x, Decimal):
        return x
    try:
        return Decimal(str(x))
    except Exception:
        try:
            return Decimal(int(x))
        except Exception:
            return Decimal(0)

def save_barang_diproduksi(report, barang_diproduksi_list):
    """
    Save or update barang_diproduksi_list into HppManufactureProduction model.
    """
    with transaction.atomic():
        for row in barang_diproduksi_list:
            product_obj = Product.objects.filter(
                name=row["product_name"], report=report
            ).first()
            if not product_obj:
                continue

            HppManufactureProduction.objects.update_or_create(
                report=report,
                product=product_obj,
                defaults={
                    "qty_diproduksi": row["qty_diproduksi"],
                    "total_produksi": row["total_produksi"],
                    "hpp_per_unit": row["hpp_per_unit"],
                },
            )