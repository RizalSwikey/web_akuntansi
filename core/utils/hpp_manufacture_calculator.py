from decimal import Decimal
from core.models import RevenueItem
from django.db import models

def calculate_hpp_manufacture(product, data):
    bb_awal = Decimal(data.get("BB_AWAL", 0))
    bb_pembelian = Decimal(data.get("BB_PEMBELIAN", 0))
    bb_akhir = Decimal(data.get("BB_AKHIR", 0))

    btkl = Decimal(data.get("BTKL", 0))
    bop = Decimal(data.get("BOP", 0))

    wip_awal = Decimal(data.get("WIP_AWAL", 0))
    wip_akhir = Decimal(data.get("WIP_AKHIR", 0))

    fg_awal = Decimal(data.get("FG_AWAL", 0))
    fg_akhir = Decimal(data.get("FG_AKHIR", 0))

    # ---------- BBB (Bahan Baku Dipakai) ----------
    bb_dipakai = bb_awal + bb_pembelian - bb_akhir

    # ---------- Total Biaya Produksi ----------
    biaya_produksi = bb_dipakai + btkl + bop

    # ---------- Barang Dalam Proses ----------
    biaya_setelah_wip = biaya_produksi + wip_awal - wip_akhir

    # ---------- HPP Barang Terjual ----------
    hpp = fg_awal + biaya_setelah_wip - fg_akhir

    # ---------- Ambil Qty Terjual ----------
    total_qty_terjual = RevenueItem.objects.filter(
        product=product,
        revenue_type="usaha"
    ).aggregate(total_qty=models.Sum("quantity"))["total_qty"] or 0

    # ---------- HPP per unit ----------
    hpp_per_unit = Decimal(0)
    if total_qty_terjual > 0:
        hpp_per_unit = hpp / Decimal(total_qty_terjual)

    return {
        "bb_dipakai": int(bb_dipakai),
        "biaya_produksi": int(biaya_produksi),
        "biaya_setelah_wip": int(biaya_setelah_wip),
        "hpp": int(hpp),
        "hpp_per_unit": float(hpp_per_unit),
        "qty_terjual": int(total_qty_terjual),

        # Debug details
        "BB_AWAL": int(bb_awal), "BB_PEMBELIAN": int(bb_pembelian), "BB_AKHIR": int(bb_akhir),
        "BTKL": int(btkl), "BOP": int(bop),
        "WIP_AWAL": int(wip_awal), "WIP_AKHIR": int(wip_akhir),
        "FG_AWAL": int(fg_awal), "FG_AKHIR": int(fg_akhir),
    }
