from django.urls import path
from . import views

urlpatterns = [
    path('acta/maintenance/<int:pk>/', views.maintenance_acta_view, name='maintenance_acta'),
    path('acta/handover/<int:pk>/', views.handover_acta_view, name='handover_acta'),
    path('export/<str:model_name>/', views.export_data_view, name='export_data'),
    
    # Frontend URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('inventory/', views.equipment_list_view, name='equipment_list'),
    path('maintenance/new/', views.maintenance_create_view, name='maintenance_create'),
]
