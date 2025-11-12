from decimal import Decimal
from django.db import transaction
from core.models import HppManufactureProduction, Product


def calculate_hpp_for_product(product, entries):
    awal = entries.get('AWAL')
    pembelian_list = entries.get('PEMBELIAN')
    akhir = entries.get('AKHIR')

    qty_awal = Decimal(awal.quantity if awal else 0)
    harga_awal = Decimal(awal.harga_satuan if awal else 0)

    total_awal = qty_awal * harga_awal

    total_pembelian_neto = Decimal(0)
    total_pembelian_qty = Decimal(0)

    for p in pembelian_list:
        pembelian_bruto = Decimal(p.quantity) * Decimal(p.harga_satuan)
        jumlah_retur_rp = Decimal(p.retur_qty) * Decimal(p.harga_satuan)
        total_pembelian = pembelian_bruto - Decimal(p.diskon) - jumlah_retur_rp + Decimal(p.ongkir)

        total_pembelian_neto += total_pembelian
        total_pembelian_qty += Decimal(p.quantity)

    barang_tersedia = total_awal + total_pembelian_neto

    qty_akhir = Decimal(akhir.quantity if akhir else 0)
    qty_tersedia = qty_awal + total_pembelian_qty

    validation_error_akhir = None
    if qty_akhir > qty_tersedia:
        validation_error_akhir = "Periksa Kembali Catatan Penjualan/Persediaan Akhir."

    if total_pembelian_qty > 0:
        unit_beli = total_pembelian_neto / total_pembelian_qty
    else:
        unit_beli = Decimal(0)

    # Perhitungan total akhir
    diff = qty_akhir - qty_awal if qty_akhir > qty_awal else Decimal(0)
    total_akhir = (qty_awal * harga_awal) + (diff * unit_beli)

    # Qty terjual
    qty_terjual = qty_tersedia - qty_akhir

    # Total HPP (COGS)
    hpp = barang_tersedia - total_akhir

    # HPP per unit terjual
    if qty_terjual > 0:
        hpp_per_unit = hpp / qty_terjual
    else:
        hpp_per_unit = 0

    return {
        "total_awal": int(total_awal),
        "total_pembelian_neto": int(total_pembelian_neto),
        "barang_tersedia": int(barang_tersedia),
        "total_akhir": int(total_akhir),
        "hpp": int(hpp),
        "hpp_per_unit": float(hpp_per_unit),

        "detail_awal": {
            "qty": int(qty_awal),
            "harga_satuan": int(harga_awal)
        } if awal else None,

        "detail_pembelian": {
            "qty": int(total_pembelian_qty),
        } if pembelian_list else None,


        "detail_akhir": {
            "qty": int(qty_akhir),
        } if akhir else None,

        "qty_terjual": int(qty_terjual),

        "validation_error_akhir": validation_error_akhir,
    }


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
    Called from hpp_manufaktur_view after barang_diproduksi_list is computed.
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
