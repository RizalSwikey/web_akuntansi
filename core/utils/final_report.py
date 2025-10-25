# core/utils/final_report.py
from django.db.models import Sum
from core.models import Product, HppEntry, RevenueItem, ExpenseItem
from core.utils.hpp_calculator import calculate_hpp_for_product


def generate_final_report_data(report):
    """
    Generate the full final report data for laporan.html and Excel export.
    Includes Pendapatan, HPP, Beban, Laba/Rugi, and HPP per produk.
    """

    # =======================
    # 1️⃣ PENDAPATAN (Revenue)
    # =======================
    total_pendapatan_usaha = (
        report.revenue_items.filter(revenue_type="usaha").aggregate(Sum("total"))["total__sum"] or 0
    )
    total_pendapatan_lain = (
        report.revenue_items.filter(revenue_type="lain").aggregate(Sum("total"))["total__sum"] or 0
    )
    jumlah_pendapatan = total_pendapatan_usaha + total_pendapatan_lain

    # =======================
    # 2️⃣ HPP (Harga Pokok Penjualan)
    # =======================
    products = Product.objects.filter(report=report)

    # Group all HPP entries per product
    entries_by_product = {}
    for entry in HppEntry.objects.filter(report=report).select_related("product"):
        pid = entry.product.id
        if pid not in entries_by_product:
            entries_by_product[pid] = {"PEMBELIAN": []}
        if entry.category == "AWAL":
            entries_by_product[pid]["AWAL"] = entry
        elif entry.category == "AKHIR":
            entries_by_product[pid]["AKHIR"] = entry
        elif entry.category == "PEMBELIAN":
            entries_by_product[pid]["PEMBELIAN"].append(entry)

    # Calculate per product HPP
    hpp_per_product = []
    total_hpp = 0

    for product in products:
        product_entries = entries_by_product.get(product.id, {"AWAL": None, "PEMBELIAN": [], "AKHIR": None})
        result = calculate_hpp_for_product(product, product_entries)

        total_awal = result.get("total_awal", 0)
        total_pembelian = result.get("total_pembelian_neto", 0)
        total_akhir = result.get("total_akhir", 0)

        qty_awal = result.get("detail_awal", {}).get("qty", 0) if result.get("detail_awal") else 0
        qty_pembelian = result.get("detail_pembelian", {}).get("qty", 0) if result.get("detail_pembelian") else 0
        qty_akhir = result.get("detail_akhir", {}).get("qty", 0) if result.get("detail_akhir") else 0

        qty_terjual = qty_awal + qty_pembelian - qty_akhir

        # 🧮 HPP total and per unit (matching your Excel formula)
        hpp_total = total_awal + total_pembelian - total_akhir
        hpp_per_unit = hpp_total / qty_terjual if qty_terjual > 0 else 0

        total_hpp += hpp_total

        hpp_per_product.append({
            "product_name": product.name,
            "hpp_per_unit": hpp_per_unit,
            "hpp": hpp_total,
            "total_awal": total_awal,
            "total_pembelian_neto": total_pembelian,
            "total_akhir": total_akhir,
            "detail_awal": {"qty": qty_awal},
            "detail_pembelian": {"qty": qty_pembelian},
            "detail_akhir": {"qty": qty_akhir},
        })

    # =======================
    # 3️⃣ BEBAN (Expenses)
    # =======================
    beban_usaha_items = report.expense_items.filter(expense_category="usaha")
    beban_lain_items = report.expense_items.filter(expense_category="lain")

    total_beban_usaha = beban_usaha_items.aggregate(Sum("total"))["total__sum"] or 0
    total_beban_lain = beban_lain_items.aggregate(Sum("total"))["total__sum"] or 0
    jumlah_beban = total_hpp + total_beban_usaha + total_beban_lain

    # =======================
    # 4️⃣ LABA / RUGI
    # =======================
    laba_sebelum_pajak = jumlah_pendapatan - jumlah_beban
    pajak_penghasilan = 0  # (you can fill later)
    laba_setelah_pajak = laba_sebelum_pajak - pajak_penghasilan

    # =======================
    # ✅ Final assembled data
    # =======================
    return {
        # Pendapatan
        "total_pendapatan_usaha": total_pendapatan_usaha,
        "total_pendapatan_lain": total_pendapatan_lain,
        "jumlah_pendapatan": jumlah_pendapatan,

        # HPP
        "hpp_total": total_hpp,
        "hpp_per_product": hpp_per_product,

        # Beban
        "beban_usaha_items": beban_usaha_items,
        "beban_lain_items": beban_lain_items,
        "total_beban_usaha_lainnya": total_beban_usaha,
        "total_beban_lain": total_beban_lain,
        "jumlah_beban": jumlah_beban,

        # Laba / Rugi
        "laba_sebelum_pajak": laba_sebelum_pajak,
        "pajak_penghasilan": pajak_penghasilan,
        "laba_setelah_pajak": laba_setelah_pajak,
    }
