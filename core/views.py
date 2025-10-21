from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# @login_required
def landing_page_view(request):
    """
    landing page
    """
    # --- Add this check ---
    # If user is already logged in, send them to profile
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
            # Render page again with error message
            return render(request, 'core/pages/login.html', {
                'error': 'Username atau password salah.'
            })

    return render(request, 'core/pages/login.html')


# @login_required
def logout_view(request):
    """
    Logs the user out and redirects to the landing page.
    """
    logout(request)
    return redirect('core:landing_page')

# @login_required
def profile_view(request):
    """
    profile page
    """
    profile_data = request.session.get('profile_data', {})

    if request.method == 'POST':
        profile_data = {
            'company_name': request.POST.get('company_name'),
            'month': request.POST.get('month'),
            'year': request.POST.get('year'),
            'business_status': request.POST.get('business_status'),
            'umkm_incentive': request.POST.get('umkm_incentive'),
            'omzet': request.POST.get('omzet'),
            'business_type': request.POST.get('business_type'),
        }
        request.session['profile_data'] = profile_data
    
        messages.success(request, 'Profil perusahaan berhasil disimpan!')
        
        return redirect('core:profile')
    
    context = {
            'profile_data': profile_data
        }
    return render(request, 'core/pages/profile.html', context)


def pendapatan_view(request):
    """
    Pendapatan page:
    - Handles adding/deleting revenue items (Usaha vs. Lain-lain) to the session.
    - Calculates totals for each category.
    """
    
    # Load existing data from session, defaulting to empty lists
    revenue_usaha = request.session.get('revenue_usaha', [])
    revenue_lain = request.session.get('revenue_lain', [])

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            try:
                data_type = request.POST.get('data_type')
                
                if data_type == 'usaha':
                    nama_produk = request.POST.get('modal-product-name')
                    quantity = int(request.POST.get('modal-quantity', 0))
                    price = int(request.POST.get('modal-price', 0))
                    
                    if not nama_produk or quantity <= 0 or price <= 0:
                        messages.error(request, 'Nama produk, kuantitas, dan harga harus diisi dengan benar.')
                    else:
                        total = quantity * price
                        revenue_usaha.append({
                            'nama': nama_produk,
                            'qty': quantity,
                            'price': price,
                            'total': total
                        })
                        request.session['revenue_usaha'] = revenue_usaha
                        messages.success(request, f'Produk "{nama_produk}" berhasil ditambahkan.')
                
                elif data_type == 'lain':
                    # Use the correct field name from your HTML
                    keterangan = request.POST.get('modal-product-name-lain') 
                    total = int(request.POST.get('modal-total', 0))
                    
                    if not keterangan or total <= 0:
                        messages.error(request, 'Keterangan dan total harus diisi dengan benar.')
                    else:
                        revenue_lain.append({
                            'nama': keterangan,
                            'total': total
                        })
                        request.session['revenue_lain'] = revenue_lain
                        messages.success(request, f'Pendapatan "{keterangan}" berhasil ditambahkan.')

            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {e}')

        elif action == 'delete_usaha':
            try:
                item_index = int(request.POST.get('item_index', -1))
                if 0 <= item_index < len(revenue_usaha):
                    removed = revenue_usaha.pop(item_index)
                    request.session['revenue_usaha'] = revenue_usaha
                    messages.success(request, f'Produk "{removed["nama"]}" berhasil dihapus.')
            except:
                messages.error(request, 'Gagal menghapus item.')
                
        elif action == 'delete_lain':
            try:
                item_index = int(request.POST.get('item_index', -1))
                if 0 <= item_index < len(revenue_lain):
                    removed = revenue_lain.pop(item_index)
                    request.session['revenue_lain'] = revenue_lain
                    messages.success(request, f'Pendapatan "{removed["nama"]}" berhasil dihapus.')
            except:
                messages.error(request, 'Gagal menghapus item.')

        # Redirect back to the same page after POST
        return redirect('core:pendapatan')

    # --- GET Request Logic ---
    
    # Calculate totals
    total_usaha = sum(item['total'] for item in revenue_usaha)
    total_lain = sum(item['total'] for item in revenue_lain)
    
    context = {
        'revenue_usaha': revenue_usaha,
        'revenue_lain': revenue_lain,
        'total_usaha': total_usaha,
        'total_lain': total_lain,
    }
    
    return render(request, 'core/pages/pendapatan.html', context)


def hpp_view(request):
    """
    hpp page (Harga Pokok Produksi)
    Handles 3 forms: Persediaan Awal, Pembelian, Persediaan Akhir.
    Calculates HPP and saves all data to session.
    """
    
    # Load all HPP data from session
    hpp_data = request.session.get('hpp_data', {
        'persediaan_awal': 0,
        'pembelian': [],
        'persediaan_akhir': 0
    })

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_awal':
            hpp_data['persediaan_awal'] = int(request.POST.get('persediaan-awal', 0))
            messages.success(request, 'Persediaan Awal berhasil disimpan.')

        elif action == 'add_pembelian':
            try:
                nama = request.POST.get('pembelian-name')
                qty = int(request.POST.get('pembelian-qty', 0))
                harga = int(request.POST.get('pembelian-price', 0))
                
                if not nama or qty <= 0 or harga <= 0:
                    messages.error(request, 'Nama, kuantitas, dan harga pembelian harus diisi with benar.')
                else:
                    total = qty * harga
                    hpp_data['pembelian'].append({'nama': nama, 'qty': qty, 'harga': harga, 'total': total})
                    messages.success(request, f'Pembelian "{nama}" berhasil ditambahkan.')
            except Exception as e:
                messages.error(request, f'Gagal menambahkan pembelian: {e}')

        elif action == 'delete_pembelian':
            try:
                item_index = int(request.POST.get('item_index', -1))
                if 0 <= item_index < len(hpp_data['pembelian']):
                    removed = hpp_data['pembelian'].pop(item_index)
                    messages.success(request, f'Pembelian "{removed["nama"]}" berhasil dihapus.')
            except:
                messages.error(request, 'Gagal menghapus item pembelian.')

        elif action == 'save_akhir':
            hpp_data['persediaan_akhir'] = int(request.POST.get('persediaan-akhir', 0))
            messages.success(request, 'Persediaan Akhir berhasil disimpan.')
        
        # Save all changes back to the session
        request.session['hpp_data'] = hpp_data
        return redirect('core:hpp')

    # --- GET Request Logic ---
    
    # Calculate totals
    total_pembelian = sum(item['total'] for item in hpp_data['pembelian'])
    barang_tersedia = hpp_data['persediaan_awal'] + total_pembelian
    
    # Calculate HPP (COGS)
    # HPP = Barang Tersedia Untuk Dijual - Persediaan Akhir
    hpp_total = barang_tersedia - hpp_data['persediaan_akhir']

    context = {
        'hpp_data': hpp_data,
        'total_pembelian': total_pembelian,
        'barang_tersedia': barang_tersedia,
        'hpp_total': hpp_total
    }
    
    return render(request, 'core/pages/hpp.html', context)


def beban_usaha_view(request):
    """
    beban usaha page
    Handles adding/deleting expense items (Usaha vs. Lain-lain) to the session.
    Calculates totals for each category.
    """
    
    # Load existing data from session, defaulting to empty lists
    beban_usaha = request.session.get('beban_usaha', [])
    beban_lain = request.session.get('beban_lain', [])

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_beban':
            try:
                beban_type = request.POST.get('beban-type')
                keterangan = request.POST.get('beban-name')
                total = int(request.POST.get('beban-total', 0))
                
                if not keterangan or total <= 0:
                    messages.error(request, 'Keterangan dan Total harus diisi dengan benar.')
                else:
                    item = {'nama': keterangan, 'total': total}
                    if beban_type == 'Beban Usaha':
                        beban_usaha.append(item)
                        request.session['beban_usaha'] = beban_usaha
                        messages.success(request, f'Beban "{keterangan}" berhasil ditambahkan.')
                    elif beban_type == 'Beban Lain-lain':
                        beban_lain.append(item)
                        request.session['beban_lain'] = beban_lain
                        messages.success(request, f'Beban "{keterangan}" berhasil ditambahkan.')
            
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {e}')

        elif action == 'delete_beban_usaha':
            try:
                item_index = int(request.POST.get('item_index', -1))
                if 0 <= item_index < len(beban_usaha):
                    removed = beban_usaha.pop(item_index)
                    request.session['beban_usaha'] = beban_usaha
                    messages.success(request, f'Beban "{removed["nama"]}" berhasil dihapus.')
            except:
                messages.error(request, 'Gagal menghapus item.')
                
        elif action == 'delete_beban_lain':
            try:
                item_index = int(request.POST.get('item_index', -1))
                if 0 <= item_index < len(beban_lain):
                    removed = beban_lain.pop(item_index)
                    request.session['beban_lain'] = beban_lain
                    messages.success(request, f'Beban "{removed["nama"]}" berhasil dihapus.')
            except:
                messages.error(request, 'Gagal menghapus item.')
        
        return redirect('core:beban_usaha')

    # --- GET Request Logic ---
    
    # Calculate totals
    total_beban_usaha = sum(item['total'] for item in beban_usaha)
    total_beban_lain = sum(item['total'] for item in beban_lain)
    grand_total_beban = total_beban_usaha + total_beban_lain

    context = {
        'beban_usaha': beban_usaha,
        'beban_lain': beban_lain,
        'total_beban_usaha': total_beban_usaha,
        'total_beban_lain': total_beban_lain,
        'grand_total_beban': grand_total_beban
    }
    
    return render(request, 'core/pages/beban_usaha.html', context)


def laporan_view(request):
    """
    laporan page
    """
    return render(request, 'core/pages/laporan.html')
