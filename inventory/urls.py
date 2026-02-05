from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard_view, name='home'),
    path('acta/maintenance/<int:pk>/', views.maintenance_acta_view, name='maintenance_acta'),
    path('acta/handover/<int:pk>/', views.handover_acta_view, name='handover_acta'),
    path('export/<str:model_name>/', views.export_data_view, name='export_data'),
    
    # Frontend URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('inventory/', views.equipment_list_view, name='equipment_list'),
    path('inventory/equipment/<int:pk>/', views.equipment_detail_view, name='equipment_detail'),
    path('inventory/equipment/<int:pk>/edit/', views.equipment_edit_view, name='equipment_edit'),
    path('inventory/new/', views.equipment_create_view, name='equipment_create'),
    path('inventory/area/new/', views.area_create_view, name='area_create'),
    path('inventory/areas/', views.area_list_view, name='area_list'),
    path('inventory/areas/', views.area_list_view, name='area_list'),
    path('inventory/areas/<int:pk>/edit/', views.area_edit_view, name='area_edit'),
    path('inventory/costcenter/new/', views.cost_center_create_view, name='cost_center_create'),
    path('inventory/costcenters/', views.cost_center_list_view, name='cost_center_list'),
    path('inventory/costcenters/<int:pk>/edit/', views.cost_center_edit_view, name='cost_center_edit'),
    path('maintenance/new/', views.maintenance_create_view, name='maintenance_create'),
    path('clients/new/', views.client_create_view, name='client_create'),
    path('handovers/new/', views.handover_create_view, name='handover_create'),
    path('handovers/', views.handover_list_view, name='handover_list'),
    path('maintenance/', views.maintenance_list_view, name='maintenance_list'),
    path('inventory/peripherals/', views.peripheral_list_view, name='peripheral_list'),
    path('inventory/peripherals/<int:pk>/', views.peripheral_detail_view, name='peripheral_detail'),
    path('inventory/peripherals/<int:pk>/edit/', views.peripheral_edit_view, name='peripheral_edit'),
    path('inventory/peripherals/new/', views.peripheral_create_view, name='peripheral_create'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/new/', views.user_create_view, name='user_create'),
]
