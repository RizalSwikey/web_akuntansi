from django.urls import path
from . import views


app_name = 'core'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('', views.landing_page_view, name='landing_page'),
    # path('profile/', views.profile_view, name='profile'),
    # path('pendapatan/', views.pendapatan_view, name='pendapatan'),
    # path('hpp/', views.hpp_view, name='hpp'),
    # path('beban-usaha/', views.beban_usaha_view, name='beban_usaha'),
    # path('laporan/', views.laporan_view, name='laporan'),

    path('reports/', views.report_list, name='report_list'),
    path('reports/new/', views.create_report, name='create_report'),



    path('reports/<int:report_id>/profile/', views.profile_view, name='profile'),
    path('reports/<int:report_id>/pendapatan/', views.pendapatan_view, name='pendapatan'),
    path('reports/<int:report_id>/hpp/', views.hpp_view, name='hpp'),
    path('reports/<int:report_id>/beban-usaha/', views.beban_usaha_view, name='beban_usaha'),
    path('reports/<int:report_id>/laporan/', views.laporan_view, name='laporan'),

    path('reports/<int:report_id>/export/pdf/', views.export_pdf, name='export_pdf'),
    path('reports/<int:report_id>/export/excel/', views.export_excel, name='export_excel'),
]

 
    
