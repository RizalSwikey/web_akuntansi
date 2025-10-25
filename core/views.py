from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum
from .models import FinancialReport, Product, RevenueItem, HppEntry, ExpenseItem
from core.utils.hpp_calculator import calculate_hpp_for_product
from core.utils.final_report import generate_final_report_data
from core.utils.excel_exporter import generate_excel_file
from core.utils.pdf_exporter import generate_pdf_file
from django.http import HttpResponse



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
        report.business_type = request.POST.get('business_type')
        report.save()
        messages.success(request, 'Profil perusahaan berhasil disimpan!')
        
        return redirect('core:pendapatan', report_id=report.id)

    return render(request, 'core/pages/profile.html', {'report': report, 'completion_status': completion_status})


@login_required(login_url='core:login')
def pendapatan_view(request, report_id):
    """
    PAGE 2: PENDAPATAN
    Gatekeeper: Must have a profile.
    Uses Product and RevenueItem models.
    """
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    completion_status = get_completion_status(report)

    # Gatekeeper: Profile must be complete
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
                        # Get or create the Product associated with this report
                        product, created = Product.objects.get_or_create(
                            report=report,
                            name=product_name
                        )
                        # Create the RevenueItem linked to the Product
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

        # Check if "next" button was clicked
        if 'next_step' in request.POST:
            # Re-check completion status AFTER potential add/delete
            completion_status = get_completion_status(report)
            if not completion_status['pendapatan']:
                 messages.warning(request, 'Harap tambahkan minimal satu pendapatan usaha sebelum melanjutkan.')
                 return redirect('core:pendapatan', report_id=report.id) # Stay here if still incomplete
            return redirect('core:hpp', report_id=report.id) # Go to next step if complete

        return redirect('core:pendapatan', report_id=report.id) # Redirect back after normal add/delete

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



@login_required(login_url='core:login')
def hpp_view(request, report_id):
    """
    PAGE 3: Harga Pokok Penjualan (HPP)
    Handles Persediaan Awal, Pembelian, Persediaan Akhir for each product.
    """
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    completion_status = get_completion_status(report)

    # --- Ensure Pendapatan Usaha Step is Complete ---
    if not completion_status['pendapatan']:
        messages.error(request, 'Harap tambahkan minimal satu pendapatan usaha terlebih dahulu.')
        return redirect('core:pendapatan', report_id=report.id)

    # --- Load Products from Pendapatan Usaha ---
    products = (
        Product.objects
        .filter(report=report, revenue_entries__revenue_type="usaha")
        .prefetch_related("revenue_entries")
        .distinct()
    )


    # --- Ensure Each Product Has All 3 HPP Categories ---
    for product in products:
        for category in ['AWAL', 'PEMBELIAN', 'AKHIR']:
            HppEntry.objects.get_or_create(
                report=report,
                product=product,
                category=category,
                defaults={
                    'keterangan': '',
                }
            )

    # --- Handle POST Actions (Edit HPP) ---
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

        return redirect('core:hpp', report_id=report.id)

    # --- Build HPP Data Dictionary ---
    hpp_data_by_product = {}
    for product in products:
        entries = HppEntry.objects.filter(product=product, report=report)
        hpp_data_by_product[product] = {
            'AWAL': entries.filter(category='AWAL').first(),
            'PEMBELIAN': entries.filter(category='PEMBELIAN'),
            'AKHIR': entries.filter(category='AKHIR').first(),
        }

    # --- Perform HPP Calculations (Refactored) ---
    grand_total_awal = grand_total_pembelian = grand_total_akhir = grand_total_barang_tersedia = grand_hpp = 0
    calculation_details = {}

    for product, entries in hpp_data_by_product.items():
        result = calculate_hpp_for_product(product, entries)
        calculation_details[product.id] = result
        print(calculation_details[product.id])
        grand_total_awal += result['total_awal']
        grand_total_pembelian += result['total_pembelian_neto']
        print(grand_total_pembelian)
        grand_total_barang_tersedia += result['barang_tersedia']
        grand_total_akhir += result['total_akhir']
        grand_hpp += result['hpp']

    # --- Render Template ---
    context = {
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
    }

    return render(request, 'core/pages/hpp.html', context)


@login_required(login_url='core:login')
def beban_usaha_view(request, report_id):
    """
    PAGE 4: BEBAN USAHA (IMPROVED)
    Gatekeeper: HPP step must be complete.
    """
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    completion_status = get_completion_status(report)

    # Gatekeeper: HPP must be complete
    if not completion_status['hpp']:
        messages.error(request, 'Harap lengkapi data HPP terlebih dahulu.')
        return redirect('core:hpp', report_id=report.id)

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
        
        # *** CONSOLIDATED DELETE ACTION ***
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
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
    
    completion_status = get_completion_status(report)

    if not completion_status['beban_usaha']:
        messages.error(request, 'Harap lengkapi data Beban Usaha terlebih dahulu.')
        return redirect('core:beban_usaha', report_id=report.id)

    data = generate_final_report_data(report)
    
    return render(request, 'core/pages/laporan.html', {
        **data,
        'report': report,
        'completion_status': completion_status,
    })



@login_required(login_url='core:login')
def export_excel(request, report_id):
    report = get_object_or_404(FinancialReport, id=report_id, user=request.user)
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
    data = generate_final_report_data(report)

    pdf_content, filename = generate_pdf_file(report, data, request=request)

    response = HttpResponse(pdf_content, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
