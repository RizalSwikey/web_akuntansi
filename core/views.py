from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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



def logout_view(request):
    """
    Logs the user out and redirects to the landing page.
    """
    logout(request)
    return redirect('core:landing_page')


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
    pendapatan page
    """
    return render(request, 'core/pages/pendapatan.html')


def hpp_view(request):
    """
    hpp page
    """
    return render(request, 'core/pages/hpp.html')


def beban_usaha_view(request):
    """
    beban usaha page
    """
    return render(request, 'core/pages/beban_usaha.html')


def laporan_view(request):
    """
    laporan page
    """
    return render(request, 'core/pages/laporan.html')
