from decimal import Decimal, InvalidOperation
from core.models import RevenueItem

def calculate_hpp_for_product(product, entries):
    """
    Matches Excel formula exactly:
    IF(akhir.qty > awal.qty + pembelian.qty, error,
       (awal.qty * awal.harga_satuan) + ((akhir.qty - awal.qty) * (total_pembelian / qty_pembelian))
    )
    """
    awal = entries.get('AWAL')
    pembelian_list = entries.get('PEMBELIAN')
    akhir = entries.get('AKHIR')

    total_awal = Decimal(awal.quantity * awal.harga_satuan) if awal else Decimal(0)

    # --- Pembelian section ---
    total_pembelian_neto = Decimal(0)
    total_pembelian_qty = Decimal(0)

    for p in pembelian_list:
        pembelian_bruto = Decimal(p.quantity) * Decimal(p.harga_satuan)
        jumlah_retur_rp = Decimal(p.retur_qty) * Decimal(p.harga_satuan)
        total_pembelian = pembelian_bruto - Decimal(p.diskon) - jumlah_retur_rp + Decimal(p.ongkir)
        total_pembelian_neto += total_pembelian
        total_pembelian_qty += Decimal(p.quantity)  # ✅ use full purchase quantity (not net of retur)

    barang_tersedia = total_awal + total_pembelian_neto

    total_akhir = Decimal(0)
    validation_error_akhir = None
    validation_error_penjualan = None

    qty_awal = Decimal(awal.quantity if awal else 0)
    qty_akhir = Decimal(akhir.quantity if akhir else 0)
    qty_tersedia = qty_awal + total_pembelian_qty

    if qty_akhir > qty_tersedia:
        validation_error_akhir = "Hitung kembali persediaan akhir (Qty Akhir > Qty Tersedia)"
    else:
        harga_awal = Decimal(awal.harga_satuan if awal else 0)
        unit_beli = (total_pembelian_neto / total_pembelian_qty) if total_pembelian_qty > 0 else Decimal(0)
        diff = qty_akhir - qty_awal if qty_akhir > qty_awal else Decimal(0)
        total_akhir = (qty_awal * harga_awal) + (diff * unit_beli)

    hpp = barang_tersedia - total_akhir

    return {
        "total_awal": int(total_awal),
        "total_pembelian_neto": int(total_pembelian_neto),
        "barang_tersedia": int(barang_tersedia),
        "total_akhir": int(total_akhir),
        "hpp": int(hpp),
        "validation_error_akhir": validation_error_akhir,
        "validation_error_penjualan": validation_error_penjualan,
    }
