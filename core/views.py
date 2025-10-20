from django.shortcuts import render



def landing_page_view(request):
    """
    landing page
    """
    return render(request, 'core/pages/landing_page.html')


def profile_view(request):
    """
    profile page
    """
    return render(request, 'core/pages/profile.html')


def dashboard_view(request):
    """
    dashboard page
    """
    return render(request, 'core/pages/dashboard.html')


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
