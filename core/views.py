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