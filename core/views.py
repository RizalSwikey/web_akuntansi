from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum
from .models import FinancialReport, Product, RevenueItem, HppEntry, ExpenseItem

from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from core.utils.hpp_calculator import calculate_hpp_for_product


# --- Helper function to get completion status ---
def get_completion_status(report):
    status = {
        'profile': False,
        'pendapatan': False,
        'hpp': False,
        'beban_usaha': True, # Beban Usaha is optional, so it's always "complete"
    }
    # Check if essential profile fields are filled
    if report and report.company_name and report.business_type:
        status['profile'] = True
        
    # Check if at least one 'usaha' (business) revenue item exists
    if status['profile'] and report.revenue_items.filter(revenue_type='usaha').exists():
        status['pendapatan'] = True
        
    # --- THIS IS THE CORRECTED HPP CHECK ---
    # Check if at least one HppEntry exists for this report
    if status['pendapatan'] and report.hpp_entries.exists():
         status['hpp'] = True
         
    return status

# --- User Auth Views (No Change) ---
def landing_page_view(request):
    if request.user.is_authenticated:
        return redirect('core:profile')
    return render(request, 'core/pages/landing_page.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('core:profile')
        else:
            return render(request, 'core/pages/login.html', {'error': 'Invalid username or password'})
    return render(request, 'core/pages/login.html')

def logout_view(request):
    logout(request)
    return redirect('core:landing_page')


# --- App Views (Refactored for Stricter Wizard Flow) ---

@login_required(login_url='core:login')
def profile_view(request):
    report, created = FinancialReport.objects.get_or_create(user=request.user)
    completion_status = get_completion_status(report)

    if request.method == 'POST':
        report.company_name = request.POST.get('company_name')
        report.month = request.POST.get('month')
        report.year = request.POST.get('year')
        report.business_status = request.POST.get('business_status')
        report.umkm_incentive = request.POST.get('umkm_incentive')
        report.omzet = request.POST.get('omzet', 0)
        report.business_type = request.POST.get('business_type')
        report.save()
        messages.success(request, 'Profil perusahaan berhasil disimpan!')
        
        # --- ALWAYS REDIRECT TO NEXT STEP ---
        return redirect('core:pendapatan')

    return render(request, 'core/pages/profile.html', {'report': report, 'completion_status': completion_status})


@login_required(login_url='core:login')
def pendapatan_view(request):
    """
    PAGE 2: PENDAPATAN
    Gatekeeper: Must have a profile.
    Uses Product and RevenueItem models.
    """
    report = get_object_or_404(FinancialReport, user=request.user)
    completion_status = get_completion_status(report)

    # Gatekeeper: Profile must be complete
    if not completion_status['profile']:
        messages.error(request, 'Harap lengkapi profil perusahaan terlebih dahulu.')
        return redirect('core:profile')

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
                 return redirect('core:pendapatan') # Stay here if still incomplete
            return redirect('core:hpp') # Go to next step if complete

        return redirect('core:pendapatan') # Redirect back after normal add/delete

    # --- GET Request Logic ---
    revenue_usaha_items = report.revenue_items.filter(revenue_type='usaha').order_by('product__name')
    revenue_lain_items = report.revenue_items.filter(revenue_type='lain').order_by('name')

    total_usaha = revenue_usaha_items.aggregate(Sum('total'))['total__sum'] or 0
    total_lain = revenue_lain_items.aggregate(Sum('total'))['total__sum'] or 0

    context = {
        'report': report,
        'revenue_usaha': revenue_usaha_items, # Pass QuerySet to template
        'revenue_lain': revenue_lain_items,   # Pass QuerySet to template
        'total_usaha': total_usaha,
        'total_lain': total_lain,
        'completion_status': completion_status
    }
    return render(request, 'core/pages/pendapatan.html', context)



@login_required(login_url='core:login')
def hpp_view(request):
    """
    PAGE 3: Harga Pokok Penjualan (HPP)
    Handles Persediaan Awal, Pembelian, Persediaan Akhir for each product.
    """
    report = get_object_or_404(FinancialReport, user=request.user)
    completion_status = get_completion_status(report)

    # --- Ensure Pendapatan Usaha Step is Complete ---
    if not completion_status['pendapatan']:
        messages.error(request, 'Harap tambahkan minimal satu pendapatan usaha terlebih dahulu.')
        return redirect('core:pendapatan')

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
                    'quantity': 0,
                    'harga_satuan': 0,
                    'diskon': 0,
                    'retur_qty': 0,
                    'ongkir': 0,
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
                return redirect('core:hpp')
            return redirect('core:beban_usaha')

        return redirect('core:hpp')

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

        grand_total_awal += result['total_awal']
        grand_total_pembelian += result['total_pembelian_neto']
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
def beban_usaha_view(request):
    """
    PAGE 4: BEBAN USAHA (IMPROVED)
    Gatekeeper: HPP step must be complete.
    """
    report = get_object_or_404(FinancialReport, user=request.user)
    completion_status = get_completion_status(report)

    # Gatekeeper: HPP must be complete
    if not completion_status['hpp']:
        messages.error(request, 'Harap lengkapi data HPP terlebih dahulu.')
        return redirect('core:hpp')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_beban':
            try:
                ExpenseItem.objects.create(
                    report=report,
                    expense_type=request.POST.get('beban-type'), # 'usaha' or 'lain'
                    name=request.POST.get('beban-name'),
                    total=int(request.POST.get('beban-total', 0))
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
            return redirect('core:laporan')
        return redirect('core:beban_usaha')

    # --- GET Request Logic ---
    beban_usaha_items = report.expense_items.filter(expense_type='usaha')
    beban_lain_items = report.expense_items.filter(expense_type='lain')
    
    total_beban_usaha = beban_usaha_items.aggregate(Sum('total'))['total__sum'] or 0
    total_beban_lain = beban_lain_items.aggregate(Sum('total'))['total__sum'] or 0
    grand_total_beban = total_beban_usaha + total_beban_lain

    context = {
        'report': report,
        'beban_usaha': beban_usaha_items, # Renamed for clarity in template
        'beban_lain': beban_lain_items,   # Renamed for clarity in template
        'total_beban_usaha': total_beban_usaha,
        'total_beban_lain': total_beban_lain,
        'grand_total_beban': grand_total_beban,
        'completion_status': completion_status
    }
    
    return render(request, 'core/pages/beban_usaha.html', context)


@login_required(login_url='core:login')
def laporan_view(request):
    report = get_object_or_404(FinancialReport, user=request.user)
    completion_status = get_completion_status(report)
    
    if not completion_status['hpp']:
        messages.error(request, 'Harap lengkapi semua langkah sebelumnya.')
        return redirect('core:hpp')

    # --- Re-calculate HPP Grand Total ---
    grand_hpp = 0
    products = Product.objects.filter(report=report, revenue_entries__revenue_type='usaha').distinct()
    for product in products:
        awal = HppEntry.objects.filter(product=product, category='AWAL').first()
        pembelian_list = HppEntry.objects.filter(product=product, category='PEMBELIAN')
        akhir = HppEntry.objects.filter(product=product, category='AKHIR').first()

        total_awal = (awal.quantity * awal.unit_price) if awal else 0
        total_pembelian_neto_product = 0
        total_pembelian_qty_product = 0
        avg_purchase_price_product = 0
        for p in pembelian_list:
            pembelian_bruto = p.quantity * p.unit_price
            retur_rp = p.return_qty * p.unit_price
            p_neto = pembelian_bruto - p.discount - retur_rp + p.shipping_cost
            total_pembelian_neto_product += p_neto
            total_pembelian_qty_product += p.quantity
            
        if total_pembelian_qty_product > 0:
            avg_purchase_price_product = Decimal(total_pembelian_neto_product - sum(p.shipping_cost for p in pembelian_list)) / Decimal(total_pembelian_qty_product)

        barang_tersedia_product = total_awal + total_pembelian_neto_product

        total_akhir_product = 0
        qty_awal = awal.quantity if awal else 0
        if akhir:
            if akhir.quantity > (qty_awal + total_pembelian_qty_product):
                pass # Error handled in hpp_view, maybe add message here too
            else:
                if akhir.quantity <= qty_awal:
                    cost_per_unit_akhir = awal.unit_price if awal and awal.unit_price > 0 else 0
                    total_akhir_product = akhir.quantity * cost_per_unit_akhir
                else:
                    cost_awal_part = total_awal
                    qty_from_purchase = akhir.quantity - qty_awal
                    cost_purchase_part = qty_from_purchase * avg_purchase_price_product
                    total_akhir_product = cost_awal_part + cost_purchase_part

        hpp_product = barang_tersedia_product - total_akhir_product
        grand_hpp += hpp_product

    # --- Laba Rugi Calculation (Using Grand HPP) ---
    total_pendapatan_usaha = report.revenue_items.filter(revenue_type='usaha').aggregate(Sum('total'))['total__sum'] or 0
    total_pendapatan_lain = report.revenue_items.filter(revenue_type='lain').aggregate(Sum('total'))['total__sum'] or 0
    jumlah_pendapatan = total_pendapatan_usaha + total_pendapatan_lain

    beban_usaha_items = report.expense_items.filter(expense_type='usaha')
    beban_lain_items = report.expense_items.filter(expense_type='lain')
    total_beban_usaha_lainnya = beban_usaha_items.aggregate(Sum('total'))['total__sum'] or 0
    total_beban_lain = beban_lain_items.aggregate(Sum('total'))['total__sum'] or 0

    jumlah_beban = grand_hpp + total_beban_usaha_lainnya + total_beban_lain # Use calculated grand_hpp
    laba_sebelum_pajak = jumlah_pendapatan - jumlah_beban
    pajak_penghasilan = 0
    laba_setelah_pajak = laba_sebelum_pajak - pajak_penghasilan

    # Need HPP details for the first part of the report page
    hpp_data = report.hpp_entries # Get all entries for detailed HPP report section
    total_pembelian_all = hpp_data.filter(category='PEMBELIAN').aggregate(Sum('total_pembelian_neto')) # Need to add total_pembelian_neto calculation to model/view
    # This part needs refinement based on how detailed HPP Laporan is needed

    context = {
        'report': report,
        # HPP Laporan Data (Simplified for now - needs full calculation like in hpp_view)
        'hpp_total': grand_hpp, # Pass the final calculated HPP
        # Laba Rugi Data
        'total_pendapatan_usaha': total_pendapatan_usaha, 'total_pendapatan_lain': total_pendapatan_lain, 'jumlah_pendapatan': jumlah_pendapatan,
        'beban_usaha_items': beban_usaha_items, 'beban_lain_items': beban_lain_items,
        'total_beban_usaha_lainnya': total_beban_usaha_lainnya, 'total_beban_lain': total_beban_lain, 'jumlah_beban': jumlah_beban,
        'laba_sebelum_pajak': laba_sebelum_pajak, 'pajak_penghasilan': pajak_penghasilan, 'laba_setelah_pajak': laba_setelah_pajak,
        'completion_status': completion_status,
    }
    return render(request, 'core/pages/laporan.html', context) # Make sure laporan.html uses these context vars