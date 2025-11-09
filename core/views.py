from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, F
from django.http import HttpResponse
from .models import FinancialReport, Product, RevenueItem, HppEntry, ExpenseItem
from .models import (
    HppManufactureMaterial,
    HppManufactureLabor,
    HppManufactureOverhead,
    HppManufactureWIP,
    HppManufactureProduction,
    HppManufactureFinishedGoods,
)
from core.utils.hpp_calculator import calculate_hpp_for_product, to_int, to_number, save_barang_diproduksi
from core.utils.final_report import generate_final_report_data
from core.utils.excel_exporter import generate_excel_file
from core.utils.pdf_exporter import generate_pdf_file


# --- Helper function to get completion status ---
def get_completion_status(report):
    status = {
        'profile': False,
        'pendapatan': False,
        'hpp': False,
        'beban_usaha': False,
    }

    # 1. Profile valid
    if report and report.company_name and report.business_type:
        status['profile'] = True

    # 2. Pendapatan minimal satu entri usaha
    if status['profile'] and report.revenue_items.filter(revenue_type='usaha').exists():
        status['pendapatan'] = True

    # 3. HPP minimal satu entri
    # (Catatan: Ini mungkin perlu disesuaikan untuk manufaktur nanti)
    if status['pendapatan'] and report.hpp_entries.exists():
        status['hpp'] = True

    # 4. Beban Usaha minimal satu entri
    if status['hpp'] and report.expense_items.filter(expense_category='usaha').exists():
        status['beban_usaha'] = True

    return status


# --- User Auth Views (No Change) ---
def landing_page_view(request):
    if request.user.is_authenticated:
        return redirect('core:report_list')
    return render(request, 'core/pages/landing_page.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('core:report_list')
        else:
            return render(request, 'core/pages/login.html', {'error': 'Invalid username or password'})
    return render(request, 'core/pages/login.html')


def logout_view(request):
    logout(request)
    return redirect('core:login')


@login_required(login_url='core:login')
def report_list(request):
    if request.method == "POST":
        delete_id = request.POST.get("delete_id")
        if delete_id:
            report_to_delete = FinancialReport.objects.filter(id=delete_id, user=request.user).first()
            if report_to_delete:
                report_to_delete.delete()
                messages.success(request, "Laporan berhasil dihapus.")
            return redirect("core:report_list")

    reports = FinancialReport.objects.filter(user=request.user).order_by('-created_at')
    # Nama template diganti ke 'report_list.html' sesuai konvensi
    return render(request, 'core/pages/report_list.html', {'reports': reports})


@login_required(login_url='core:login')
def create_report(request):
    report = FinancialReport.objects.create(user=request.user)
    messages.success(request, "Laporan baru berhasil dibuat. Silakan isi profil perusahaan.")
    return redirect('core:profile', report_id=report.id)

# --- App Views (Refactored for Stricter Wizard Flow) ---

@login_required(login_url='core:login')
def profile_view(request, report_id):
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    completion_status = get_completion_status(report)

    if request.method == 'POST':
        report.company_name = request.POST.get('company_name')
        report.month = request.POST.get('month')
        report.year = request.POST.get('year')
        report.business_status = request.POST.get('business_status')
        report.ptkp_status = request.POST.get('ptkp_status')
        report.umkm_incentive = request.POST.get('umkm_incentive')
        report.omzet = request.POST.get('omzet', 0)
        report.business_type = request.POST.get('business_type') # INI PENTING
        report.save()
        messages.success(request, 'Profil perusahaan berhasil disimpan!')
        
        return redirect('core:pendapatan', report_id=report.id)

    return render(request, 'core/pages/profile.html', {'report': report, 'completion_status': completion_status})


@login_required(login_url='core:login')
def pendapatan_view(request, report_id):
    """
    PAGE 2: PENDAPATAN (Universal)
    """
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    completion_status = get_completion_status(report)

    if not completion_status['profile']:
        messages.error(request, 'Harap lengkapi profil perusahaan terlebih dahulu.')
        return redirect('core:profile', report_id=report.id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            try:
                data_type = request.POST.get('data_type') # 'usaha' or 'lain'

                if data_type == 'usaha':
                    product_name = request.POST.get('modal-product-name')
                    quantity = int(request.POST.get('modal-quantity', 0))
                    selling_price = int(request.POST.get('modal-price', 0))

                    if not product_name or quantity <= 0 or selling_price <= 0:
                        messages.error(request, 'Nama produk, kuantitas, dan harga jual harus diisi dengan benar.')
                    else:
                        product, created = Product.objects.get_or_create(
                            report=report,
                            name=product_name
                        )
                        RevenueItem.objects.create(
                            report=report,
                            revenue_type=data_type,
                            product=product,
                            quantity=quantity,
                            selling_price=selling_price
                        )
                        messages.success(request, f'Pendapatan usaha "{product_name}" berhasil ditambahkan.')

                elif data_type == 'lain':
                    item_name = request.POST.get('modal-product-name-lain')
                    total = int(request.POST.get('modal-total', 0))

                    if not item_name or total <= 0:
                         messages.error(request, 'Keterangan dan total harus diisi dengan benar.')
                    else:
                        RevenueItem.objects.create(
                            report=report,
                            revenue_type=data_type,
                            name=item_name,
                            total=total
                        )
                        messages.success(request, f'Pendapatan lain-lain "{item_name}" berhasil ditambahkan.')

            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {e}')

        elif action == 'delete_revenue_item':
            try:
                item_id = int(request.POST.get('item_id', -1))
                item = RevenueItem.objects.get(id=item_id, report=report)
                item_name = item.name
                item.delete()
                messages.success(request, f'Pendapatan "{item_name}" berhasil dihapus.')
            except RevenueItem.DoesNotExist:
                 messages.error(request, 'Item pendapatan tidak ditemukan.')
            except Exception as e:
                messages.error(request, f'Gagal menghapus item: {e}')

        if 'next_step' in request.POST:
            completion_status = get_completion_status(report)
            if not completion_status['pendapatan']:
                 messages.warning(request, 'Harap tambahkan minimal satu pendapatan usaha sebelum melanjutkan.')
                 return redirect('core:pendapatan', report_id=report.id) 
            # Arahkan ke HPP (view HPP akan menangani routing dagang/manufaktur)
            return redirect('core:hpp', report_id=report.id) 

        return redirect('core:pendapatan', report_id=report.id) 

    # --- GET Request Logic ---
    revenue_usaha_items = report.revenue_items.filter(revenue_type='usaha').order_by('product__name')
    revenue_lain_items = report.revenue_items.filter(revenue_type='lain').order_by('name')
    total_usaha = revenue_usaha_items.aggregate(Sum('total'))['total__sum'] or 0
    total_lain = revenue_lain_items.aggregate(Sum('total'))['total__sum'] or 0

    context = {
        'report': report,
        'revenue_usaha': revenue_usaha_items,
        'revenue_lain': revenue_lain_items,
        'total_usaha': total_usaha,
        'total_lain': total_lain,
        'completion_status': completion_status
    }
    return render(request, 'core/pages/pendapatan.html', context)


# =============================================
# MULAI PERUBAHAN
# =============================================
@login_required(login_url='core:login')
def hpp_view(request, report_id):
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)

    # Check pendapatan first
    completion_status = get_completion_status(report)
    if not completion_status['pendapatan']:
        messages.error(request, 'Harap tambahkan minimal satu pendapatan usaha terlebih dahulu.')
        return redirect('core:pendapatan', report_id=report.id)

    # Route based on business type
    if report.business_type == 'manufaktur':
        return redirect('core:hpp_manufaktur', report_id=report_id)
    else:
        return redirect('core:hpp_dagang', report_id=report_id)



@login_required(login_url='core:login')
def hpp_dagang_view(request, report_id):
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    completion_status = get_completion_status(report)

    products = (
        Product.objects
        .filter(report=report, revenue_entries__revenue_type="usaha")
        .prefetch_related("revenue_entries")
        .distinct()
    )

    # Ensure base entries exist
    for product in products:
        for category in ['AWAL', 'PEMBELIAN', 'AKHIR']:
            HppEntry.objects.get_or_create(
                report=report,
                product=product,
                category=category,
                defaults={'keterangan': ''}
            )

    if request.method == 'POST':
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')

        if action == 'edit_hpp_entry':
            product = get_object_or_404(Product, id=product_id, report=report)
            category = request.POST.get('category')

            try:
                HppEntry.objects.update_or_create(
                    report=report,
                    product=product,
                    category=category,
                    defaults={
                        'quantity': int(request.POST.get('quantity', 0)),
                        'harga_satuan': int(request.POST.get('harga_satuan', 0)),
                        'diskon': int(request.POST.get('diskon', 0)) if category == 'PEMBELIAN' else 0,
                        'retur_qty': int(request.POST.get('retur_qty', 0)) if category == 'PEMBELIAN' else 0,
                        'ongkir': int(request.POST.get('ongkir', 0)) if category == 'PEMBELIAN' else 0,
                        'keterangan': request.POST.get('keterangan', ''),
                    }
                )
                messages.success(request, f"Data HPP {category} untuk {product.name} berhasil disimpan.")
            except Exception as e:
                messages.error(request, f"Gagal menyimpan data HPP: {e}")

        elif 'next_step' in request.POST:
            if not completion_status['hpp']:
                messages.warning(request, 'Isi minimal satu data HPP sebelum lanjut.')
                return redirect('core:hpp', report_id=report.id)
            return redirect('core:beban_usaha', report_id=report.id)

        return redirect('core:hpp_dagang', report_id=report.id)

    # Build HPP detail
    hpp_data_by_product = {}
    for product in products:
        entries = HppEntry.objects.filter(product=product, report=report)
        hpp_data_by_product[product] = {
            'AWAL': entries.filter(category='AWAL').first(),
            'PEMBELIAN': entries.filter(category='PEMBELIAN'),
            'AKHIR': entries.filter(category='AKHIR').first(),
        }

    # Calculate totals
    grand_total_awal = grand_total_pembelian = grand_total_akhir = grand_total_barang_tersedia = grand_hpp = 0
    calculation_details = {}

    for product, entries in hpp_data_by_product.items():
        result = calculate_hpp_for_product(product, entries)
        calculation_details[product.id] = result
        grand_total_awal += result['total_awal']
        grand_total_pembelian += result['total_pembelian_neto']
        grand_total_barang_tersedia += result['barang_tersedia']
        grand_total_akhir += result['total_akhir']
        grand_hpp += result['hpp']

    return render(request, 'core/pages/hpp.html', {
        'report': report,
        'products': products,
        'hpp_data_by_product': hpp_data_by_product,
        'calculation_details': calculation_details,
        'grand_total_awal': grand_total_awal,
        'grand_total_pembelian_neto': grand_total_pembelian,
        'grand_total_barang_tersedia': grand_total_barang_tersedia,
        'grand_total_akhir': grand_total_akhir,
        'grand_hpp': grand_hpp,
        'completion_status': completion_status,
    })


@login_required(login_url='core:login')
def hpp_manufaktur_view(request, report_id):
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    completion_status = get_completion_status(report)
    products = Product.objects.filter(report=report)

    barang_diproduksi_list = []

    # ===========================
    # HANDLE POST (SAVE DATA)
    # ===========================
    if request.method == "POST":
        action = request.POST.get("action")

        # --- BAHAN BAKU ---
        if action == "add_bb":
            product_id = request.POST.get("product_id")
            product = get_object_or_404(Product, id=product_id, report=report)

            tipe = request.POST.get("type")  # BB_AWAL / BB_PEMBELIAN / BB_AKHIR
            nama_bb = request.POST.get("nama_bahan_baku", "").strip()
            keterangan = request.POST.get("keterangan", "").strip()

            qty = to_int(request.POST.get("quantity"))
            harga = to_int(request.POST.get("harga_satuan"))
            diskon = to_int(request.POST.get("diskon"))
            retur_qty = to_int(request.POST.get("retur_qty"))
            retur_amount_post = to_int(request.POST.get("retur_amount"))
            retur_amount = to_int(retur_amount_post) if retur_amount_post != 0 else (retur_qty * harga)
            ongkir = to_int(request.POST.get("ongkir"))

            if retur_qty > qty:
                messages.error(request, "Retur (Qty) tidak boleh lebih besar dari Kuantitas.")
                return redirect("core:hpp_manufaktur", report_id=report.id)

            if tipe in ["BB_AWAL", "BB_AKHIR"]:
                total = qty * harga
            else:
                total = (qty * harga) - diskon - retur_amount + ongkir

            HppManufactureMaterial.objects.create(
                report=report,
                product=product,
                nama_bahan_baku=nama_bb,
                type=tipe,
                quantity=qty,
                harga_satuan=harga,
                diskon=diskon,
                retur_qty=retur_qty,
                retur_amount=retur_amount,
                ongkir=ongkir,
                total=total,
                keterangan=keterangan,
            )

            messages.success(request, "Data bahan baku berhasil disimpan.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        if action == "edit_bb":
            item = get_object_or_404(HppManufactureMaterial, id=request.POST.get("item_id"), report=report)

            item.type = request.POST.get("type")
            item.product_id = request.POST.get("product_id")
            item.nama_bahan_baku = request.POST.get("nama_bahan_baku")
            item.quantity = to_int(request.POST.get("quantity"))
            item.harga_satuan = to_int(request.POST.get("harga_satuan"))
            item.diskon = to_int(request.POST.get("diskon"))
            item.retur_qty = to_int(request.POST.get("retur_qty"))
            item.retur_amount = to_int(request.POST.get("retur_amount"))
            item.ongkir = to_int(request.POST.get("ongkir"))
            item.keterangan = request.POST.get("keterangan", "")

            if item.type in ["BB_AWAL", "BB_AKHIR"]:
                item.total = item.quantity * item.harga_satuan
            else:
                item.total = (item.quantity * item.harga_satuan) - item.diskon - item.retur_amount + item.ongkir

            item.save()
            messages.success(request, "Data bahan baku berhasil diperbarui.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        if action == "delete_bb":
            HppManufactureMaterial.objects.filter(id=request.POST.get("item_id"), report=report).delete()
            messages.success(request, "Data bahan baku berhasil dihapus.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        # --- BDP / WIP ---
        if action in ["add_wip", "edit_wip"]:
            item_id = request.POST.get("item_id")
            tipe = request.POST.get("type")
            qty = to_int(request.POST.get("quantity"))
            harga = to_int(request.POST.get("harga_satuan"))
            keterangan = request.POST.get("keterangan", "")
            product_id = request.POST.get("product_id")
            total = qty * harga

            if action == "add_wip":
                HppManufactureWIP.objects.create(
                    report=report,
                    product_id=product_id,
                    type=tipe,
                    quantity=qty,
                    harga_satuan=harga,
                    total=total,
                    keterangan=keterangan,
                )
                messages.success(request, "Data BDP berhasil ditambahkan.")
            else:
                item = get_object_or_404(HppManufactureWIP, id=item_id)
                item.type = tipe
                item.product_id = product_id
                item.quantity = qty
                item.harga_satuan = harga
                item.total = total
                item.keterangan = keterangan
                item.save()
                messages.success(request, "Data BDP berhasil diperbarui.")

            return redirect("core:hpp_manufaktur", report_id=report.id)

        if action == "delete_wip":
            item_id = request.POST.get("item_id")
            get_object_or_404(HppManufactureWIP, id=item_id).delete()
            messages.success(request, "Data BDP berhasil dihapus.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        # --- BTKL ---
        if action in ["add_btkl", "edit_btkl"]:
            item_id = request.POST.get("item_id")
            product_id = request.POST.get("product_id")
            jenis_tenaga_kerja = request.POST.get("jenis_tenaga_kerja", "")
            qty = to_int(request.POST.get("quantity"))
            harga = to_int(request.POST.get("harga_satuan"))
            keterangan = request.POST.get("keterangan", "")
            total = qty * harga

            if action == "add_btkl":
                HppManufactureLabor.objects.create(
                    report=report,
                    product_id=product_id,
                    jenis_tenaga_kerja=jenis_tenaga_kerja,
                    quantity=qty,
                    harga_satuan=harga,
                    total=total,
                    keterangan=keterangan,
                )
                messages.success(request, "Data BTKL berhasil ditambahkan.")
            else:
                item = get_object_or_404(HppManufactureLabor, id=item_id)
                item.product_id = product_id
                item.jenis_tenaga_kerja = jenis_tenaga_kerja
                item.quantity = qty
                item.harga_satuan = harga
                item.total = total
                item.keterangan = keterangan
                item.save()
                messages.success(request, "Data BTKL berhasil diperbarui.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        if action == "delete_btkl":
            item_id = request.POST.get("item_id")
            get_object_or_404(HppManufactureLabor, id=item_id).delete()
            messages.success(request, "Data BTKL berhasil dihapus.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        # --- BOP ---
        if action == "add_bop":
            nama_biaya = request.POST.get("nama_biaya", "")
            product_id = request.POST.get("product_id") or None
            quantity = int(request.POST.get("quantity", 0))
            harga_satuan = int(request.POST.get("harga_satuan", 0))
            keterangan = request.POST.get("keterangan", "")
            total = quantity * harga_satuan

            HppManufactureOverhead.objects.create(
                report=report,
                product_id=product_id,
                nama_biaya=nama_biaya,
                quantity=quantity,
                harga_satuan=harga_satuan,
                total=total,
                keterangan=keterangan,
            )
            messages.success(request, "Data BOP berhasil disimpan.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        if action == "edit_bop":
            item_id = request.POST.get("item_id")
            item = get_object_or_404(HppManufactureOverhead, id=item_id, report=report)
            item.nama_biaya = request.POST.get("nama_biaya", "")
            item.product_id = request.POST.get("product_id") or None
            item.quantity = int(request.POST.get("quantity", 0))
            item.harga_satuan = int(request.POST.get("harga_satuan", 0))
            item.keterangan = request.POST.get("keterangan", "")
            item.total = item.quantity * item.harga_satuan
            item.save()
            messages.success(request, "Data BOP berhasil diperbarui.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        if action == "delete_bop":
            item_id = request.POST.get("item_id")
            HppManufactureOverhead.objects.filter(id=item_id, report=report).delete()
            messages.success(request, "Data BOP berhasil dihapus.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        # --- BARANG JADI (FG_AWAL & FG_AKHIR) ---
        if action in ["add_fg", "edit_fg"]:
            item_id = request.POST.get("item_id")
            tipe_data = request.POST.get("tipe_data")
            product_id = request.POST.get("product_id")
            qty = to_int(request.POST.get("kuantitas"))
            harga_satuan = to_int(request.POST.get("harga_satuan"))
            keterangan = request.POST.get("keterangan", "")

            total = qty * harga_satuan
            status = "OK"

            if tipe_data == "AKHIR_BJ":
                # Calculate automatically
                bj_awal_map = {x.product.id: x for x in HppManufactureFinishedGoods.objects.filter(report=report, type="FG_AWAL")}
                produksi_map = {x["product_name"]: x for x in barang_diproduksi_list}

                awal = bj_awal_map.get(int(product_id))
                qty_awal = awal.quantity if awal else 0
                harga_awal = awal.harga_satuan if awal else 0

                product_obj = Product.objects.filter(id=product_id).first()
                product_name = product_obj.name if product_obj else None

                produksi = produksi_map.get(product_name, {})
                qty_produksi = produksi.get("qty_diproduksi", 0)
                harga_produksi = produksi.get("hpp_per_unit", 0)

                if qty == 0:
                    status = "-"
                    total = 0
                elif qty > (qty_awal + qty_produksi):
                    status = "Periksa Kembali Jumlah Persediaan Barang Jadi Akhir"
                    total = 0
                else:
                    total = (qty_awal * harga_awal) + ((qty - qty_awal) * harga_produksi)
                    status = "OK"

            tipe = "FG_AWAL" if tipe_data == "AWAL_BJ" else "FG_AKHIR"

            if action == "add_fg":
                HppManufactureFinishedGoods.objects.create(
                    report=report,
                    product_id=product_id,
                    type=tipe,
                    quantity=qty,
                    harga_satuan=harga_satuan,
                    total=total,
                    keterangan=keterangan,
                )
                messages.success(request, f"Data Barang Jadi ({'Akhir' if tipe == 'FG_AKHIR' else 'Awal'}) berhasil disimpan.")
            else:
                item = get_object_or_404(HppManufactureFinishedGoods, id=item_id)
                item.type = tipe
                item.product_id = product_id
                item.quantity = qty
                item.harga_satuan = harga_satuan
                item.total = total
                item.keterangan = keterangan
                item.save()
                messages.success(request, "Data Barang Jadi berhasil diperbarui.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        if action == "delete_fg":
            item_id = request.POST.get("item_id")
            get_object_or_404(HppManufactureFinishedGoods, id=item_id).delete()
            messages.success(request, "Data Persediaan Barang Jadi berhasil dihapus.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        if "next_step" in request.POST:
            return redirect("core:beban_usaha", report_id=report.id)
    
    # --- Load All Data for Template ---
    bb_awal = HppManufactureMaterial.objects.filter(report=report, type="BB_AWAL")
    bb_pembelian = HppManufactureMaterial.objects.filter(report=report, type="BB_PEMBELIAN")
    bb_akhir = HppManufactureMaterial.objects.filter(report=report, type="BB_AKHIR")
    bdp_awal = HppManufactureWIP.objects.filter(report=report, type="WIP_AWAL")
    bdp_akhir = HppManufactureWIP.objects.filter(report=report, type="WIP_AKHIR")
    btkl_items = HppManufactureLabor.objects.filter(report=report)
    bop_items = HppManufactureOverhead.objects.filter(report=report)
    bj_awal = HppManufactureFinishedGoods.objects.filter(report=report, type="FG_AWAL")
    bj_akhir = HppManufactureFinishedGoods.objects.filter(report=report, type="FG_AKHIR")

     # Helper to group totals per product
    def grouped_totals(queryset):
        if not queryset.exists():
            return []
        return (
            queryset.values("product", product_name=F("product__name"))
            .annotate(total=Sum("total"))
            .order_by("product__name")
        )

    totals_awal_per_produk = grouped_totals(bb_awal)
    totals_pembelian_per_produk = grouped_totals(bb_pembelian)
    totals_akhir_per_produk = grouped_totals(bb_akhir)
    totals_bdp_awal_per_produk = grouped_totals(bdp_awal)
    totals_bdp_akhir_per_produk = grouped_totals(bdp_akhir)
    totals_btkl_per_produk = grouped_totals(btkl_items)
    totals_bop_per_produk = grouped_totals(bop_items)
    totals_bj_awal_per_produk = grouped_totals(bj_awal)
    totals_bj_akhir_per_produk = grouped_totals(bj_akhir)

    # ======================================================
    # STEP 2 — BARANG DIPRODUKSI CALCULATION (used later)
    # ======================================================
    def map_totals(qs):
        return {row["product"]: row["total"] for row in qs}

    bb_awal_map = map_totals(totals_awal_per_produk)
    bb_pembelian_map = map_totals(totals_pembelian_per_produk)
    bb_akhir_map = map_totals(totals_akhir_per_produk)
    bdp_awal_map = map_totals(totals_bdp_awal_per_produk)
    bdp_akhir_map = map_totals(totals_bdp_akhir_per_produk)
    btkl_map = map_totals(totals_btkl_per_produk)
    bop_map = map_totals(totals_bop_per_produk)

    def map_qty(qs):
        return {w.product.id: w.quantity for w in qs}

    bdp_awal_qty = map_qty(bdp_awal)
    bdp_akhir_qty = map_qty(bdp_akhir)

    product_ids = set(bb_awal_map.keys()) | set(bb_pembelian_map.keys()) | set(bb_akhir_map.keys())

    for pid in product_ids:
        product = Product.objects.filter(id=pid).first()
        if not product:
            continue

        qty_awal = bdp_awal_qty.get(pid, 0)
        qty_akhir = bdp_akhir_qty.get(pid, 0)
        qty_diproduksi = max(qty_akhir - qty_awal, 0)

        total_produksi = (
            (bb_awal_map.get(pid, 0) + bb_pembelian_map.get(pid, 0) - bb_akhir_map.get(pid, 0))
            + (bdp_akhir_map.get(pid, 0) - bdp_awal_map.get(pid, 0))
            + btkl_map.get(pid, 0)
            + bop_map.get(pid, 0)
        )

        hpp_per_unit = total_produksi / qty_diproduksi if qty_diproduksi else 0

        barang_diproduksi_list.append({
            "product_name": product.name,
            "qty_awal": qty_awal,
            "qty_akhir": qty_akhir,
            "qty_diproduksi": qty_diproduksi,
            "total_produksi": total_produksi,
            "hpp_per_unit": hpp_per_unit,
        })
    
    if request.method == "POST" or not HppManufactureProduction.objects.filter(report=report).exists():
        save_barang_diproduksi(report, barang_diproduksi_list)

    total_barang_diproduksi = sum(to_number(row.get("total_produksi", 0)) for row in barang_diproduksi_list)
    total_barang_diproduksi = int(total_barang_diproduksi)

    # ======================================================
    # STEP 3 — HANDLE POST ACTIONS (Now barang_diproduksi_list is READY)
    # ======================================================
    if request.method == "POST":
        action = request.POST.get("action")

        # ------------------------
        # BARANG JADI
        # ------------------------
        if action in ["add_fg", "edit_fg"]:
            item_id = request.POST.get("item_id")
            tipe_data = request.POST.get("tipe_data")
            product_id = request.POST.get("product_id")
            qty = to_int(request.POST.get("kuantitas"))
            harga_satuan = to_int(request.POST.get("harga_satuan"))
            keterangan = request.POST.get("keterangan", "")

            total = qty * harga_satuan
            status = "OK"

            if tipe_data == "AKHIR_BJ":
                bj_awal_map = {x.product.id: x for x in bj_awal}
                produksi_map = {x["product_name"]: x for x in barang_diproduksi_list}

                awal = bj_awal_map.get(int(product_id))
                qty_awal = awal.quantity if awal else 0
                harga_awal = awal.harga_satuan if awal else 0

                product_obj = Product.objects.filter(id=product_id).first()
                product_name = product_obj.name if product_obj else None
                produksi = produksi_map.get(product_name, {})
                qty_produksi = produksi.get("qty_diproduksi", 0)
                harga_produksi = produksi.get("hpp_per_unit", 0)

                if qty == 0:
                    status = "-"
                    total = 0
                elif qty > (qty_awal + qty_produksi):
                    status = "Periksa Kembali Jumlah Persediaan Barang Jadi Akhir"
                    total = 0
                else:
                    total = (qty_awal * harga_awal) + ((qty - qty_awal) * harga_produksi)
                    status = "OK"

            tipe = "FG_AWAL" if tipe_data == "AWAL_BJ" else "FG_AKHIR"

            if action == "add_fg":
                HppManufactureFinishedGoods.objects.create(
                    report=report,
                    product_id=product_id,
                    type=tipe,
                    quantity=qty,
                    harga_satuan=harga_satuan,
                    total=total,
                    keterangan=keterangan,
                    status=status,
                )
                messages.success(
                    request,
                    f"Data Persediaan Barang Jadi ({'Akhir' if tipe == 'FG_AKHIR' else 'Awal'}) berhasil disimpan."
                )
            else:
                item = get_object_or_404(HppManufactureFinishedGoods, id=item_id)
                item.type = tipe
                item.product_id = product_id
                item.quantity = qty
                item.harga_satuan = harga_satuan
                item.total = total
                item.keterangan = keterangan
                item.status = status  # ✅ update too
                item.save()
                messages.success(request, "Data Barang Jadi berhasil diperbarui.")

            return redirect("core:hpp_manufaktur", report_id=report.id)

        if action == "delete_fg":
            item_id = request.POST.get("item_id")
            get_object_or_404(HppManufactureFinishedGoods, id=item_id).delete()
            messages.success(request, "Data Barang Jadi berhasil dihapus.")
            return redirect("core:hpp_manufaktur", report_id=report.id)

        # handle next step
        if "next_step" in request.POST:
            return redirect("core:beban_usaha", report_id=report.id)


    # SUMS
    total_bahan_baku_awal = bb_awal.aggregate(Sum('total'))['total__sum'] or 0
    total_bahan_baku_pembelian = bb_pembelian.aggregate(Sum('total'))['total__sum'] or 0
    total_bahan_baku_akhir = bb_akhir.aggregate(Sum('total'))['total__sum'] or 0

    total_bdp_awal = bdp_awal.aggregate(Sum('total'))['total__sum'] or 0
    total_bdp_akhir = bdp_akhir.aggregate(Sum('total'))['total__sum'] or 0

    total_btkl = btkl_items.aggregate(Sum('total'))['total__sum'] or 0
    total_bop = bop_items.aggregate(Sum('total'))['total__sum'] or 0

    total_bj_awal = bj_awal.aggregate(Sum('total'))['total__sum'] or 0
    total_bj_akhir = bj_akhir.aggregate(Sum('total'))['total__sum'] or 0

    # ======================================================
    # STEP 4 — FINAL CALC FOR TEMPLATE DISPLAY (bj_akhir_calc)
    # ======================================================
    bj_awal_map = {x.product.id: x for x in bj_awal}
    produksi_map = {x["product_name"]: x for x in barang_diproduksi_list}

    for akhir in bj_akhir:
        product_name = akhir.product.name if akhir.product else None
        if not product_name:
            akhir.status = "-"
            akhir.total_akhir = 0
            continue

        qty_akhir = akhir.quantity or 0

        awal = bj_awal_map.get(akhir.product.id)
        qty_awal = awal.quantity if awal else 0
        harga_awal = awal.harga_satuan if awal else 0

        produksi = produksi_map.get(product_name, {})
        qty_produksi = produksi.get("qty_diproduksi", 0)
        harga_produksi = produksi.get("hpp_per_unit", 0)

        # Apply logic
        if qty_akhir == 0:
            akhir.status = "-"
            akhir.total_akhir = 0
        elif qty_akhir > (qty_awal + qty_produksi):
            akhir.status = "Periksa Kembali Jumlah Persediaan Barang Jadi Akhir"
            akhir.total_akhir = 0
        else:
            akhir.total_akhir = (qty_awal * harga_awal) + ((qty_akhir - qty_awal) * harga_produksi)
            akhir.status = "OK"

    # subtotal
    total_bj_akhir_calc = sum(getattr(x, "total_akhir", 0) for x in bj_akhir)


    # ======================================================
    # STEP 5 — RENDER TEMPLATE
    # ======================================================
    return render(request, "core/pages/hpp_manufaktur.html", {
        "report": report,
        "products": products,
        "completion_status": completion_status,

        "bb_awal": bb_awal,
        "bb_pembelian": bb_pembelian,
        "bb_akhir": bb_akhir,
        "bdp_awal": bdp_awal,
        "bdp_akhir": bdp_akhir,
        "btkl_items": btkl_items,
        "bop_items": bop_items,
        "bj_awal": bj_awal,
        "bj_akhir": bj_akhir,

        # Totals
        "totals_awal_per_produk": totals_awal_per_produk,
        "totals_pembelian_per_produk": totals_pembelian_per_produk,
        "totals_akhir_per_produk": totals_akhir_per_produk,
        "totals_bdp_awal_per_produk": totals_bdp_awal_per_produk,
        "totals_bdp_akhir_per_produk": totals_bdp_akhir_per_produk,
        "totals_btkl_per_produk": totals_btkl_per_produk,
        "totals_bop_per_produk": totals_bop_per_produk,
        "totals_bj_awal_per_produk": totals_bj_awal_per_produk,
        "totals_bj_akhir_per_produk": totals_bj_akhir_per_produk,

        "barang_diproduksi_list": barang_diproduksi_list,
        "total_barang_diproduksi": total_barang_diproduksi,
    
        # SUMS
        "total_bahan_baku_awal": total_bahan_baku_awal,
        "total_bahan_baku_pembelian": total_bahan_baku_pembelian,
        "total_bahan_baku_akhir": total_bahan_baku_akhir,
        "total_bdp_awal": total_bdp_awal,
        "total_bdp_akhir": total_bdp_akhir,
        "total_btkl": total_btkl,
        "total_bop": total_bop,
        "total_bj_awal": total_bj_awal,
        "total_bj_akhir": total_bj_akhir,
        "total_bj_akhir_calc": total_bj_akhir_calc,
    })


@login_required(login_url='core:login')
def beban_usaha_view(request, report_id):
    """
    PAGE 4: BEBAN USAHA (LOGIKA BARU)
    Juga bertindak sebagai router.
    """
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    completion_status = get_completion_status(report)

    # Gatekeeper: HPP must be complete
    if not completion_status['hpp']:
        messages.error(request, 'Harap lengkapi data HPP terlebih dahulu.')
        # Arahkan kembali ke HPP (yang akan me-routing otomatis)
        return redirect('core:hpp', report_id=report.id) 

    # ======================================================
    # LOGIKA PERCABANGAN (BARU)
    # ======================================================
    if report.business_type == 'manufaktur':
        # --- LOGIKA UNTUK MANUFAKTUR ---
        
        # (Saat ini kosong, hanya untuk front-end)
        
        context = {
            'report': report,
            'completion_status': completion_status,
        }
        # Render template BARU
        return render(request, 'core/pages/beban_usaha_manufaktur.html', context)

    else:
        # ======================================================
        # LOGIKA DAGANG (KODE ANDA YANG SUDAH ADA)
        # ======================================================
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'add_beban':
                try:
                    ExpenseItem.objects.create(
                        report=report,
                        expense_category=request.POST.get('kategori_beban'),
                        expense_type=request.POST.get('jenis_beban'),
                        name=request.POST.get('nama_beban'),
                        total=int(request.POST.get('total_beban', 0))
                    )
                    messages.success(request, 'Beban berhasil ditambahkan.')
                except Exception as e:
                    messages.error(request, f'Terjadi kesalahan: {e}')
            
            elif action == 'delete_beban_item':
                try:
                    item_id = int(request.POST.get('item_id', -1))
                    item = ExpenseItem.objects.get(id=item_id, report=report)
                    item_name = item.name
                    item.delete()
                    messages.success(request, f'Beban "{item_name}" berhasil dihapus.')
                except:
                    messages.error(request, 'Gagal menghapus item.')
            
            if 'next_step' in request.POST:
                return redirect('core:laporan', report_id=report.id)
            return redirect('core:beban_usaha', report_id=report.id)

        # --- GET Request Logic ---
        beban_usaha_items = report.expense_items.filter(expense_category='usaha')
        beban_lain_items = report.expense_items.filter(expense_category='lain')
        total_beban_usaha = beban_usaha_items.aggregate(Sum('total'))['total__sum'] or 0
        total_beban_lain = beban_lain_items.aggregate(Sum('total'))['total__sum'] or 0

        context = {
            'report': report,
            'beban_usaha': beban_usaha_items,
            'beban_lain': beban_lain_items,
            'completion_status': completion_status,
            'total_beban_usaha': total_beban_usaha,
            'total_beban_lain': total_beban_lain,
        }
        
        return render(request, 'core/pages/beban_usaha.html', context)


@login_required(login_url='core:login')
def laporan_view(request, report_id):
    """
    PAGE 5: LAPORAN (LOGIKA BARU)
    Juga bertindak sebagai router.
    """
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    completion_status = get_completion_status(report)

    if not completion_status['beban_usaha']:
        messages.error(request, 'Harap lengkapi data Beban Usaha terlebih dahulu.')
        return redirect('core:beban_usaha', report_id=report.id)

    # ======================================================
    # LOGIKA PERCABANGAN (BARU)
    # ======================================================
    if report.business_type == 'manufaktur':
        # --- LOGIKA UNTUK MANUFAKTUR ---
        
        # (Backend Anda akan membuat fungsi kalkulasi baru 
        #  misalnya generate_final_report_data_manufaktur() nanti)
        # data = generate_final_report_data_manufaktur(report) 
        
        context = {
            # **data,
            'report': report,
            'completion_status': completion_status,
        }
        # Render template BARU
        return render(request, 'core/pages/laporan_manufaktur.html', context)
        
    else:
        # ======================================================
        # LOGIKA DAGANG (KODE ANDA YANG SUDAH ADA)
        # ======================================================
        data = generate_final_report_data(report) # Ini fungsi Dagang
        
        return render(request, 'core/pages/laporan.html', {
            **data,
            'report': report,
            'completion_status': completion_status,
        })

# =============================================
# AKHIR PERUBAHAN
# =============================================


@login_required(login_url='core:login')
def export_excel(request, report_id):
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    
    # Nanti ini juga perlu logika if/else
    content, filename = generate_excel_file(report)
    
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@login_required(login_url='core:login')
def export_pdf(request, report_id):
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)

    # Nanti ini juga perlu logika if/else
    data = generate_final_report_data(report)
    pdf_content, filename = generate_pdf_file(report, data, request=request)

    response = HttpResponse(pdf_content, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response