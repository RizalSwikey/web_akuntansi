from django.db.models import Sum
from core.models import (
    Product, HppEntry, RevenueItem, ExpenseItem,
    HppManufactureMaterial, HppManufactureLabor, HppManufactureOverhead,
    HppManufactureWIP, HppManufactureProduction, HppManufactureFinishedGoods
)
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
        total_pembelian_neto = result.get("total_pembelian_neto", 0)
        total_akhir = result.get("total_akhir", 0)

        qty_awal = result.get("detail_awal", {}).get("qty", 0) if result.get("detail_awal") else 0
        qty_pembelian = result.get("detail_pembelian", {}).get("qty", 0) if result.get("detail_pembelian") else 0
        qty_akhir = result.get("detail_akhir", {}).get("qty", 0) if result.get("detail_akhir") else 0

        qty_terjual = qty_awal + qty_pembelian - qty_akhir

        # 🧮 HPP total and per unit (matching your Excel formula)
        hpp_total = total_awal + total_pembelian_neto - total_akhir
        hpp_per_unit = hpp_total / qty_terjual if qty_terjual > 0 else 0

        total_hpp += hpp_total

        hpp_per_product.append({
            "product_name": product.name,
            "hpp_per_unit": hpp_per_unit,
            "hpp": hpp_total,
            "total_awal": total_awal,
            "total_pembelian_neto": total_pembelian_neto,
            "total_akhir": total_akhir,
            "detail_awal": {"qty": qty_awal},
            "detail_pembelian": {"qty": qty_pembelian},
            "detail_akhir": {"qty": qty_akhir},
        })

    # --- Summarize HPP totals for laporan.html and laporan_pdf.html ---
    total_persediaan_awal = sum(p['total_awal'] for p in hpp_per_product)
    total_pembelian_neto = sum(p['total_pembelian_neto'] for p in hpp_per_product)
    total_persediaan_akhir = sum(p['total_akhir'] for p in hpp_per_product)
    total_hpp = sum(p['hpp'] for p in hpp_per_product)
    barang_siap_dijual = total_persediaan_awal + total_pembelian_neto

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

    return {
        "total_pendapatan_usaha": total_pendapatan_usaha,
        "total_pendapatan_lain": total_pendapatan_lain,
        "jumlah_pendapatan": jumlah_pendapatan,

        "total_hpp": total_hpp,
        "hpp_per_product": hpp_per_product,
        "total_persediaan_awal": total_persediaan_awal,
        "total_pembelian_neto": total_pembelian_neto,
        "barang_siap_dijual": barang_siap_dijual,
        "total_persediaan_akhir": total_persediaan_akhir,

        # Keep your existing values
        "beban_usaha_items": beban_usaha_items,
        "beban_lain_items": beban_lain_items,
        "total_beban_usaha": total_beban_usaha,
        "total_beban_lain": total_beban_lain,
        "jumlah_beban": jumlah_beban,
        "laba_sebelum_pajak": laba_sebelum_pajak,
        "pajak_penghasilan": pajak_penghasilan,
        "laba_setelah_pajak": laba_setelah_pajak,
    }


def get_manufaktur_report_context(report):
    """
    Helper function to calculate all final report data for Manufaktur.
    This is used by the web view, PDF export, and Excel export.
    """
    
    # --- 1. CALCULATE HARGA POKOK PRODUKSI (COGM) ---
    total_bb_awal = HppManufactureMaterial.objects.filter(report=report, type="BB_AWAL").aggregate(Sum('total'))['total__sum'] or 0
    total_bb_pembelian = HppManufactureMaterial.objects.filter(report=report, type="BB_PEMBELIAN").aggregate(Sum('total'))['total__sum'] or 0
    total_bb_akhir = HppManufactureMaterial.objects.filter(report=report, type="BB_AKHIR").aggregate(Sum('total'))['total__sum'] or 0
    total_bbb = total_bb_awal + total_bb_pembelian - total_bb_akhir
    
    total_btkl = HppManufactureLabor.objects.filter(report=report).aggregate(Sum('total'))['total__sum'] or 0
    
    bop_items = HppManufactureOverhead.objects.filter(report=report).order_by('nama_biaya')
    total_bop = bop_items.aggregate(Sum('total'))['total__sum'] or 0
    
    total_biaya_produksi = total_bbb + total_btkl + total_bop
    
    total_bdp_awal = HppManufactureWIP.objects.filter(report=report, type="WIP_AWAL").aggregate(Sum('total'))['total__sum'] or 0
    total_bdp_akhir = HppManufactureWIP.objects.filter(report=report, type="WIP_AKHIR").aggregate(Sum('total'))['total__sum'] or 0
    
    cogm = total_biaya_produksi + total_bdp_awal - total_bdp_akhir

    # --- 2. CALCULATE HARGA POKOK PENJUALAN (HPP / COGS) ---
    total_bj_awal = HppManufactureFinishedGoods.objects.filter(report=report, type="FG_AWAL").aggregate(Sum('total'))['total__sum'] or 0
    total_bj_akhir = HppManufactureFinishedGoods.objects.filter(report=report, type="FG_AKHIR").aggregate(Sum('total'))['total__sum'] or 0
    
    barang_siap_dijual = cogm + total_bj_awal
    total_hpp = barang_siap_dijual - total_bj_akhir
    
    hpp_per_product = HppManufactureProduction.objects.filter(report=report).order_by('product__name')
    
    # --- 3. CALCULATE LABA RUGI ---
    total_pendapatan_usaha = RevenueItem.objects.filter(report=report, revenue_type='usaha').aggregate(Sum('total'))['total__sum'] or 0
    total_pendapatan_lain = RevenueItem.objects.filter(report=report, revenue_type='lain').aggregate(Sum('total'))['total__sum'] or 0
    jumlah_pendapatan = total_pendapatan_usaha + total_pendapatan_lain
    
    beban_usaha_items = ExpenseItem.objects.filter(report=report, expense_category='usaha').order_by('name')
    total_beban_usaha_lainnya = beban_usaha_items.aggregate(Sum('total'))['total__sum'] or 0
    
    beban_lain_items = ExpenseItem.objects.filter(report=report, expense_category='lain').order_by('name')
    total_beban_lain = beban_lain_items.aggregate(Sum('total'))['total__sum'] or 0
    
    jumlah_beban = total_hpp + total_beban_usaha_lainnya + total_beban_lain
    
    laba_sebelum_pajak = jumlah_pendapatan - jumlah_beban
    
    # TODO: Implement tax calculation
    pajak_penghasilan = 0 
    laba_setelah_pajak = laba_sebelum_pajak - pajak_penghasilan

    # --- 4. RETURN CONTEXT DICTIONARY ---
    context = {
        'report': report,
        'total_bb_awal': total_bb_awal,
        'total_bb_pembelian': total_bb_pembelian,
        'total_bb_akhir': total_bb_akhir,
        'total_bbb': total_bbb,
        'total_btkl': total_btkl,
        'bop_items': bop_items,
        'total_bop': total_bop,
        'total_biaya_produksi': total_biaya_produksi,
        'total_bdp_awal': total_bdp_awal,
        'total_bdp_akhir': total_bdp_akhir,
        'cogm': cogm,
        'total_bj_awal': total_bj_awal,
        'total_bj_akhir': total_bj_akhir,
        'barang_siap_dijual': barang_siap_dijual,
        'total_hpp': total_hpp,
        'hpp_per_product': hpp_per_product,
        'total_pendapatan_usaha': total_pendapatan_usaha,
        'total_pendapatan_lain': total_pendapatan_lain,
        'jumlah_pendapatan': jumlah_pendapatan,
        'hpp_total': total_hpp,
        'beban_usaha_items': beban_usaha_items,
        'total_beban_usaha_lainnya': total_beban_usaha_lainnya,
        'beban_lain_items': beban_lain_items,
        'total_beban_lain': total_beban_lain,
        'jumlah_beban': jumlah_beban,
        'laba_sebelum_pajak': laba_sebelum_pajak,
        'pajak_penghasilan': pajak_penghasilan,
        'laba_setelah_pajak': laba_setelah_pajak,
    }
    return context