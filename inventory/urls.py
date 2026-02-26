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
    path('inventory/import/', views.import_equipment_view, name='import_equipment'),
    path('inventory/', views.equipment_list_view, name='equipment_list'),
    path('inventory/equipment/<int:pk>/qr/', views.generate_qr_view, name='equipment_qr'),
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
    path('maintenance/<int:pk>/success/', views.maintenance_success_view, name='maintenance_success'),
    path('clients/new/', views.client_create_view, name='client_create'),
    path('handovers/new/', views.handover_create_view, name='handover_create'),
    path('handovers/<int:pk>/success/', views.handover_success_view, name='handover_success'),
    path('handovers/', views.handover_list_view, name='handover_list'),
    path('handovers/', views.handover_list_view, name='handover_list'),
    path('maintenance/', views.maintenance_list_view, name='maintenance_list'),
    path('maintenance/schedule/', views.maintenance_schedule_view, name='maintenance_schedule'),
    path('maintenance/schedule/toggle/', views.toggle_schedule_view, name='toggle_schedule'),
    path('reports/', views.reports_dashboard_view, name='reports_dashboard'),
    path('reports/export/pdf/', views.export_report_pdf, name='export_report_pdf'),
    path('inventory/peripherals/', views.peripheral_list_view, name='peripheral_list'),
    path('inventory/peripherals/<int:pk>/', views.peripheral_detail_view, name='peripheral_detail'),
    path('inventory/peripherals/<int:pk>/edit/', views.peripheral_edit_view, name='peripheral_edit'),
    path('inventory/peripherals/new/', views.peripheral_create_view, name='peripheral_create'),
    path('inventory/peripherals/types/new/', views.peripheral_type_create_view, name='peripheral_type_create'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/new/', views.user_create_view, name='user_create'),

    # Equipment Rounds URLs
    path('rounds/', views.equipment_round_list_view, name='equipment_round_list'),
    path('rounds/new/', views.equipment_round_create_view, name='equipment_round_create'),

    # Footer informational pages
    path('support/', views.support_view, name='support_help_desk'),
    path('manual/', views.manual_view, name='user_manual'),
    path('privacy/', views.privacy_policy_view, name='privacy_policy'),
]
