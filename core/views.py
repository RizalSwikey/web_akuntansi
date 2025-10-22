from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, F, Avg, Case, When, Value, DecimalField
from django.db.models.functions import Coalesce
import decimal
from .models import FinancialReport, Product, RevenueItem, HppEntry, ExpenseItem


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
        print("DATA TYPE RECEIVED:", request.POST.get('data_type'))

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
    PAGE 3: HPP (Harga Pokok Produksi) - Refactored for Manufacturing ('Dagang' type)
    Gatekeeper: Pendapatan must be complete.
    Handles modal edits for HppEntry objects per product.
    Performs complex calculations.
    """
    report = get_object_or_404(FinancialReport, user=request.user)
    completion_status = get_completion_status(report)

    # Gatekeeper: Pendapatan must be complete
    if not completion_status['pendapatan']:
        messages.error(request, 'Harap tambahkan minimal satu pendapatan usaha terlebih dahulu.')
        return redirect('core:pendapatan')

    if request.method == 'POST':
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id, report=report)

        if action == 'edit_hpp_entry':
            category = request.POST.get('category') # AWAL, PEMBELIAN, AKHIR
            hpp_entry_id = request.POST.get('hpp_entry_id') # Might be empty if creating new

            try:
                # Get or Create the HppEntry for this specific product and category
                if hpp_entry_id:
                     entry = HppEntry.objects.get(id=hpp_entry_id, product=product, category=category)
                else:
                    # Use update_or_create to handle potential race conditions or initial creation
                     entry, created = HppEntry.objects.update_or_create(
                         report=report, product=product, category=category,
                         defaults={} # We'll set fields below
                     )

                # Update fields based on category from modal form
                entry.quantity = int(request.POST.get('quantity', 0))
                entry.notes = request.POST.get('keterangan', '') # Use 'notes' if you used English names
                entry.unit_price = int(request.POST.get('harga_satuan', 0)) # Use 'unit_price'

                if category == 'PEMBELIAN':
                    entry.discount = int(request.POST.get('diskon', 0)) # Use 'discount'
                    entry.return_qty = int(request.POST.get('retur_qty', 0)) # Use 'return_quantity'
                    entry.shipping_cost = int(request.POST.get('ongkir', 0)) # Use 'shipping_cost'

                entry.save()
                messages.success(request, f'Data HPP untuk {product.name} ({entry.get_category_display()}) berhasil disimpan.')

            except Exception as e:
                messages.error(request, f'Gagal menyimpan data HPP: {e}')

        # Note: We might need a separate delete action, especially for PEMBELIAN if multiple are allowed per product
        # elif action == 'delete_hpp_pembelian':
        #    ...

        if 'next_step' in request.POST:
             # Re-check completion status AFTER potential add/edit
            completion_status = get_completion_status(report)
            if not completion_status['hpp']:
                 messages.warning(request, 'Harap isi minimal satu data HPP (misal: Persediaan Awal) sebelum melanjutkan.')
                 return redirect('core:hpp') # Stay here if still incomplete
            return redirect('core:beban_usaha')
        return redirect('core:hpp')

    # --- GET Request Logic ---
    # Fetch all products associated with 'usaha' revenue items for this report
    products = Product.objects.filter(report=report, revenue_entries__revenue_type='usaha').distinct()

    # Prepare data structure for the template {product: {AWAL: entry, PEMBELIAN: [entries], AKHIR: entry}}
    hpp_data_by_product = {}
    for product in products:
        entries = HppEntry.objects.filter(product=product)
        hpp_data_by_product[product] = {
            'AWAL': entries.filter(category='AWAL').first(),
            'PEMBELIAN': entries.filter(category='PEMBELIAN'), # Can have multiple purchases
            'AKHIR': entries.filter(category='AKHIR').first(),
        }

    # --- Perform Calculations (Per Product and Grand Totals) ---
    grand_total_awal = 0
    grand_total_pembelian_neto = 0
    grand_total_barang_tersedia = 0
    grand_total_akhir = 0
    grand_hpp = 0
    calculation_details = {} # Store per-product results for display

    for product, entries in hpp_data_by_product.items():
        awal = entries.get('AWAL')
        pembelian_list = entries.get('PEMBELIAN')
        akhir = entries.get('AKHIR')

        # 1. Calculate Total Awal (Using harga_satuan)
        total_awal = (awal.quantity * awal.harga_satuan) if awal else 0
        grand_total_awal += total_awal

        # 2. Calculate Total Pembelian Neto (Using harga_satuan)
        total_pembelian_neto_product = 0
        total_pembelian_qty_product = 0
        total_pembelian_cost_product = 0 # Sum of (qty * price) for purchases
        for p in pembelian_list:
            pembelian_bruto = p.quantity * p.harga_satuan
            # Formula: (7) = (6) x (4) -> (Retur Qty * Harga Satuan)
            retur_rp = p.retur_qty * p.harga_satuan
            # Formula: (9) = (2)x(4) - (5) - (7) + (8) -> (Qty*Harga) - Diskon - ReturRp + Ongkir
            p_neto = pembelian_bruto - p.diskon - retur_rp + p.ongkir
            total_pembelian_neto_product += p_neto
            total_pembelian_qty_product += p.quantity
            total_pembelian_cost_product += pembelian_bruto # Sum costs before discounts/returns/shipping for avg calc

        grand_total_pembelian_neto += total_pembelian_neto_product

        # Calculate average purchase price (needed for Akhir calc) - based on cost before other factors
        avg_purchase_price_product = decimal.Decimal(0)
        if total_pembelian_qty_product > 0:
             # Avg Price = Total Bruto Cost / Total Qty Purchased
            avg_purchase_price_product = decimal.Decimal(total_pembelian_cost_product) / decimal.Decimal(total_pembelian_qty_product)


        # 3. Calculate Barang Tersedia
        barang_tersedia_product = total_awal + total_pembelian_neto_product # Should this use bruto? Check formula logic
        # Let's assume Barang Tersedia uses Neto Pembelian for now based on HPP = BT - Akhir
        grand_total_barang_tersedia += barang_tersedia_product

        # 4. Calculate Total Akhir (using Average Cost logic) and perform validation (Using harga_satuan)
        total_akhir_product = decimal.Decimal(0) # Use Decimal for precision
        validation_error_akhir = None
        validation_error_penjualan = None
        qty_awal = awal.quantity if awal else 0
        qty_tersedia = qty_awal + total_pembelian_qty_product

        if akhir:
            # Validation 1: Qty Akhir <= Qty Tersedia
            if akhir.quantity > qty_tersedia:
                validation_error_akhir = "Hitung kembali persediaan akhir (Qty Akhir > Qty Tersedia)"
            else:
                 # Formula (simplified average cost):
                 # (Qty Awal * Harga Awal) + (Qty Akhir - Qty Awal) * Avg Harga Pembelian
                 if akhir.quantity <= qty_awal:
                      # If ending inventory is less than or equal to beginning, use beginning cost
                     cost_per_unit_akhir = decimal.Decimal(awal.harga_satuan) if awal and awal.harga_satuan > 0 else decimal.Decimal(0)
                     total_akhir_product = decimal.Decimal(akhir.quantity) * cost_per_unit_akhir
                 else:
                      # If ending inventory is more than beginning, use weighted average logic
                      cost_awal_part = decimal.Decimal(total_awal)
                      qty_from_purchase = akhir.quantity - qty_awal
                      cost_purchase_part = decimal.Decimal(qty_from_purchase) * avg_purchase_price_product
                      total_akhir_product = cost_awal_part + cost_purchase_part

            # Validation 2: Check against Sales Quantity
            try:
                # Use filter().first() in case multiple revenue entries exist (though unlikely with unique constraint)
                revenue_entry = RevenueItem.objects.filter(product=product, revenue_type='usaha').first()
                if revenue_entry:
                    qty_sold = revenue_entry.quantity
                    qty_used_or_sold = qty_tersedia - akhir.quantity
                    # Allow for rounding differences slightly? Or enforce exact match?
                    if qty_used_or_sold != qty_sold:
                         validation_error_penjualan = f"Periksa Qty Jual ({qty_sold}) vs Qty Keluar ({qty_used_or_sold}). Qty Tersedia: {qty_tersedia}, Qty Akhir: {akhir.quantity}"
            except RevenueItem.DoesNotExist:
                 pass # No sales recorded for this product
        
        # Convert Decimal back to int/BigInt if necessary for storage/display consistency, or keep Decimal
        grand_total_akhir += int(total_akhir_product) # Convert here for summing


        # 5. Calculate HPP per product
        hpp_product = barang_tersedia_product - int(total_akhir_product) # Ensure consistent types
        grand_hpp += hpp_product

        calculation_details[product.id] = {
            'total_awal': total_awal,
            'total_pembelian_neto': total_pembelian_neto_product,
            'barang_tersedia': barang_tersedia_product,
            'total_akhir': int(total_akhir_product), # Store as int
            'hpp': hpp_product,
            'avg_purchase_price': avg_purchase_price_product, # For debugging/display if needed
            'validation_error_akhir': validation_error_akhir,
            'validation_error_penjualan': validation_error_penjualan,
        }

    print("Products found for HPP:", products)
    print("Number of products:", products.count())

    context = {
        'report': report,
        'products': products,
        'hpp_data_by_product': hpp_data_by_product,
        'calculation_details': calculation_details,
        'grand_total_awal': grand_total_awal,
        'grand_total_pembelian_neto': grand_total_pembelian_neto,
        'grand_total_barang_tersedia': grand_total_barang_tersedia,
        'grand_total_akhir': grand_total_akhir,
        'grand_hpp': grand_hpp,
        'completion_status': completion_status
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
            avg_purchase_price_product = decimal.Decimal(total_pembelian_neto_product - sum(p.shipping_cost for p in pembelian_list)) / decimal.Decimal(total_pembelian_qty_product)

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