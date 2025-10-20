from django.urls import path
from . import views


app_name = 'core'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('', views.landing_page_view, name='landing_page'),
    path('profile/', views.profile_view, name='profile'),
    path('pendapatan/', views.pendapatan_view, name='pendapatan'),
    path('hpp/', views.hpp_view, name='hpp'),
    path('beban-usaha/', views.beban_usaha_view, name='beban_usaha'),
    path('laporan/', views.laporan_view, name='laporan'),
]